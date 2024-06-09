"""Pipeline for running all NLP analysis and updating the database
"""

import argparse
import logging
import os
from datetime import datetime
from functools import partial

import polars as pl
from pydo import Client

from civiclens.nlp import titles
from civiclens.nlp.comments import get_doc_comments, rep_comment_analysis
from civiclens.nlp.models import sentence_transformer, sentiment_pipeline
from civiclens.nlp.tools import RepComments, sentiment_analysis
from civiclens.nlp.topics import HDAModel, LabelChain, topic_comment_analysis
from civiclens.utils import constants
from civiclens.utils.database_access import Database, pull_data, upload_comments


# config logging
logger = logging.getLogger(__name__)
os.makedirs("nlp_logs", exist_ok=True)
logging.getLogger("gensim").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    filename=f'nlp_logs/{datetime.now().strftime("%Y-%m-%d")}_run.log',
    encoding="utf-8",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


parser = argparse.ArgumentParser()
parser.add_argument("--refresh", action="store_true", required=False)
parser.add_argument("--cloud", action="store_true", required=False)


def doc_generator(df: pl.DataFrame, doc_idx: int = 0):
    """creates a doc generator"""
    for row in df.iter_rows():
        yield row[doc_idx]


def get_last_update():
    """gets the timestamp of last update"""
    new_date = None
    nlp_updated_query = """SELECT last_updated
                        FROM regulations_nlpoutput
                        ORDER BY last_updated ASC LIMIT 1"""
    db_date = Database()
    last_updated = pull_data(
        query=nlp_updated_query,
        connection=db_date,
        schema=["last_updated"],
    )

    if last_updated.is_empty():
        return new_date

    last_updated = last_updated[0, "last_updated"]
    if last_updated:
        new_date = last_updated.strftime("%Y-%m-%d %H:%M:%S")

    return new_date


def docs_have_titles():
    """Gets all docs that have nlp titles already"""
    titles_query = """SELECT document_id, doc_plain_english_title
                    FROM regulations_nlpoutput
                    WHERE doc_plain_english_title IS NOT NULL"""
    db_title = Database()
    docs_with_titles = pull_data(
        query=titles_query, connection=db_title, return_type="list"
    )

    return dict(docs_with_titles)


if __name__ == "__main__":
    args = parser.parse_args()

    if args.refresh:
        docs_with_titles = []
        docs_to_update = """SELECT document_id
        FROM regulations_comment
        GROUP BY document_id;
        """
    else:
        args = parser.parse_args()
        last_updated = get_last_update()
        doc_titles = docs_have_titles()
        # what docs need comment nlp update
        if last_updated is not None:
            docs_to_update = f"""SELECT document_id
                FROM regulations_comment rc1
                WHERE posted_date >= TIMESTAMP '{last_updated}'
                GROUP BY document_id
                HAVING COUNT(*) > 20
                AND COUNT(*) >= 0.1 * (
                SELECT COUNT(*)
                FROM regulations_comment rc2
                WHERE rc2.document_id = rc1.document_id
                );"""  # noqa: E702, E231, E241, E202
        else:
            docs_to_update = """SELECT document_id
            FROM regulations_comment rc1
            GROUP BY document_id
            HAVING COUNT(*) > 20;
            """

    db_docs = Database()
    df_docs_to_update = pull_data(
        query=docs_to_update, connection=db_docs, schema=["document"]
    )
    documents = doc_generator(df_docs_to_update)
    title_creator = titles.TitleChain()
    labeler = LabelChain()
    sentiment_analyzer = partial(
        sentiment_analysis, pipeline=sentiment_pipeline
    )

    for doc_id in documents:
        # generate title if there is not already one
        comment_data = RepComments(document_id=doc_id)

        comment_data.summary = titles.get_doc_summary(id=doc_id)[0, "summary"]
        current_title = doc_titles.get(doc_id, None)

        if (not current_title or args.refresh) and comment_data.summary:
            comment_data.doc_plain_english_title = title_creator.invoke(
                paragraph=comment_data.summary
            )
        else:
            comment_data.doc_plain_english_title = current_title

        # do rep comment nlp
        comment_df = get_doc_comments(doc_id)
        if comment_df.is_empty():
            upload_comments(Database(), comment_data)
            continue

        comment_data = rep_comment_analysis(
            comment_data, comment_df, sentence_transformer
        )

        # topic modeling
        topic_model = HDAModel()
        comment_data = topic_comment_analysis(
            comment_data,
            model=topic_model,
            labeler=labeler,
            sentiment_analyzer=sentiment_analyzer,
        )

        logger.info(f"Proccessed document: {doc_id}")
        upload_comments(Database(), comment_data)

    if args.cloud:
        # kill instance after job finishes
        do_client = Client(token=constants.DIGITAL_OCEAN)
        do_client.droplets.destroy(droplet_id=constants.DROPLET_ID)
