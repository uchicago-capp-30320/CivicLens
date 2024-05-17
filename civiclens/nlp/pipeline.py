from functools import partial

import polars as pl
from sentence_transformers import SentenceTransformer

from civiclens.nlp import comments, titles
from civiclens.nlp.models import sentiment_pipeline
from civiclens.nlp.tools import sentiment_analysis
from civiclens.nlp.topics import LabelChain, TopicModel, topic_comment_analysis
from civiclens.utils.database_access import Database, pull_data, upload_comments


def doc_generator(df: pl.DataFrame):
    """creates a doc generator"""
    for row in df.iter_rows():
        yield (row)


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
    titles_query = """SELECT document_id
                    FROM regulations_nlpoutput
                    WHERE doc_plain_english_title IS NOT NULL"""
    db_title = Database()
    docs_with_titles = pull_data(
        query=titles_query, connection=db_title, schema=["document_id"]
    )
    docs_with_titles = docs_with_titles["document_id"].to_list()
    return docs_with_titles


if __name__ == "__main__":
    last_updated = get_last_update()
    docs_with_titles = docs_have_titles()

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
            GROUP BY document_id
            HAVING COUNT(*) > 20 )
        """
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
    doc_gen = doc_generator(df_docs_to_update)

    title_creator = titles.TitleChain()
    labeler = LabelChain()
    sbert_model = SentenceTransformer("all-mpnet-base-v2")
    sentiment_analyzer = partial(sentiment_analysis, pipeline=sentiment_pipeline)

    for _ in range(len(docs_to_update)):
        try:
            # do rep comment nlp
            doc_id = next(doc_gen)[0]
            comment_data = comments.rep_comment_analysis(doc_id, sbert_model)

            # generate title if there is not already one
            comment_data.summary = titles.get_doc_summary(id=doc_id)[0, "summary"]
            if doc_id not in docs_with_titles and comment_data.summary:
                new_title = title_creator.invoke(paragraph=comment_data.summary)
                comment_data.doc_plain_english_title = new_title

            topic_model = TopicModel()
            comment_data = topic_comment_analysis(
                comment_data,
                model=topic_model,
                labeler=labeler,
                sentiment_analyzer=sentiment_analyzer,
            )

            # TODO update upload function to search column
            # TODO logging for upload errors
            upload_comments(Database(), comment_data)

        except StopIteration:
            print("NLP Update Completed")
            break
