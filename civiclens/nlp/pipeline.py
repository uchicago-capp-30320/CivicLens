import datetime

from ..utils.database_access import Database, pull_data
from . import comments, titles


def doc_generator(df):
    for row in df.iter_rows():
        yield (row)


if __name__ == "__main__":
    # get time nlp last updated
    nlp_updated_query = """SELECT nlp_last_updated
                        FROM regulations_nlpoutput
                        ORDER BY nlp_last_updated ASC LIMIT 1"""

    db_date = Database()
    last_updated = pull_data(
        query=nlp_updated_query,
        connection=db_date.conn,
        schema=["nlp_last_updated"],
    )[0, "nlp_last_updated"]

    if last_updated is not None:
        last_updated = last_updated.strftime("%Y-%m-%d %H:%M:%S")

    # what docs dont need new titles
    titles_query = """SELECT document_id
                    FROM regulations_nlpoutput
                    WHERE doc_plain_english_title IS NOT NULL"""
    db_title = Database()
    docs_with_titles = pull_data(
        query=titles_query, connection=db_title.conn, schema=["document_id"]
    )
    docs_with_titles = docs_with_titles["document_id"].to_list()

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
            HAVING COUNT(*) > 20
        )
        """
    else:
        docs_to_update = """SELECT document_id
        FROM regulations_comment rc1
        GROUP BY document_id
        HAVING COUNT(*) > 20;
        """

    db_docs = Database()
    df_docs_to_update = pull_data(
        query=docs_to_update, connection=db_docs.conn, schema=["document"]
    )
    doc_gen = doc_generator(df_docs_to_update)

    title_creator = titles.TitleChain()

    for _ in range(len(docs_to_update)):
        try:
            # do rep comment nlp
            doc_id = next(doc_gen)[0]
            comment_data = comments.rep_comment_analysis(doc_id)

            # generate title if there is not already one
            if doc_id not in docs_with_titles:
                doc_summary = titles.get_doc_summary(id=doc_id)[0, "summary"]
                if doc_summary is not None:
                    new_title = title_creator.invoke(paragraph=doc_summary)
                    comment_data.doc_plain_english_title = new_title

            # TODO call topic code
            # Get the current timestamp of nlp update
            updated = datetime.datetime.now()
            # TODO update nlp table with comment_data, updated time, and topic
            # code
            # TODO update document table with topic search terms
        except StopIteration:
            print("NLP Update Completed")
            break
