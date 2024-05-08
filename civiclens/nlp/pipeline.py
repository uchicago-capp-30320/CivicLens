import datetime

from ..utils.database_access import pull_data
from . import comments, titles


def doc_generator(df):
    for row in df.iter_rows():
        yield (row)


if __name__ == "__main__":
    # get time nlp last updated
    nlp_updated_query = """SELECT nlp_last_updated
                        FROM regulations_nlpoutput
                        ORDER BY nlp_last_updated ASC LIMIT 1"""
    # last_updated = pull_data(nlp_updated_query, ['nlp_last_updated'])

    # make it a string, using a random date for now
    last_updated = datetime.datetime(2024, 3, 20, 4, 0)
    last_updated = last_updated.strftime("%Y-%m-%d %H:%M:%S")

    # what docs dont need new titles
    titles_query = """SELECT document_id
                    FROM regulations_nlpoutput
                    WHERE doc_plain_english_title IS NOT NULL"""
    docs_with_titles = pull_data(titles_query, ["document_id"])
    docs_with_titles = docs_with_titles["document_id"].to_list()

    # what docs need comment nlp update
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
    df_docs_to_update = pull_data(docs_to_update, ["document"])
    doc_gen = doc_generator(df_docs_to_update)

    title_creator = titles.TitleChain()

    # for _ in range(len(docs_to_update)):
    for _ in range(1):
        try:
            doc_id = next(doc_gen)[0]
            comment_data = comments.rep_comment_analysis(doc_id)

            if doc_id not in docs_with_titles:
                print("call title creator, handle null summary")
                doc_summary = titles.get_doc_summary(id=doc_id)[0, "summary"]
                if doc_summary is not None:
                    new_title = title_creator.invoke(paragraph=doc_summary)
                    comment_data.doc_plain_english_title = new_title
            # TODO call topic code
            # TODO update nlp table - do this with andrew
            # Get the current date and time of nlp update
            updated = datetime.datetime.now()
            print(updated)
            print(comment_data.doc_plain_english_title)
            print(comment_data.doc_comments)
            print(comment_data.rep_comments)
            print(
                comment_data.num_total_comments,
                comment_data.num_unique_comments,
                comment_data.num_representative_comment,
            )
        except StopIteration:
            print("NLP Update Completed")
            break
