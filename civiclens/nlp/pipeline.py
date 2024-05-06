# get all documents that meet a criteria of comments (pull nlp title as well)
# create a doc id generator, loop through:
# if doc id doesn't have  nlp title and does have a summary
# # (where does nlp title live?):
# create document title (how to insert and where?)
# pull all comments for the doc id
# run comments through the comments and topics functions
# update nlp table using df
import datetime

import comments
import titles

from ..utils.database_access import pull_data


def doc_generator(df):
    for row in df.iter_rows():
        yield (row)


if __name__ == "__main__":
    # get time nlp last updated
    nlp_updated_query = """SELECT nlp_last_updated
                        FROM regulations_nlpoutput
                        ORDER BY nlp_last_updated ASC LIMIT 1"""
    # last_updated = pull_data(nlp_updated_query, ['nlp_last_updated']) - later

    # make it a string
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

    # should we do document titles even if they don't meet the threshold of a
    # comment? like should document titles
    # just loop through documents separately from the comment loop and add
    # titles
    for _ in range(len(docs_to_update)):
        try:
            doc_id = next(doc_gen)[0]
            if doc_id not in docs_with_titles:
                print("call title creator, handle null summary")
                new_title = titles.get_doc_summary(id=doc_id)
            # call comment code, topic code, return df
            df_comments = comments.get_doc_comments()
            df_rep_analysis = comments.rep_comment_analysis(
                df_comments
            )  # fix comments code
            # call topics code, return df
            # make sure all fields are correct in df
            # update nlp table - do this with andrew
            # change comments code so that it takes in an id only,
            # runs from a function
        except StopIteration:
            print("NLP Update Completed")
            break
