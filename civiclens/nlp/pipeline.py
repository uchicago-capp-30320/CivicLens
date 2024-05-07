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

    # should we do document titles even if they don't meet the threshold of a
    # comment? like should document titles
    # just loop through documents separately from the comment loop and add
    # titles

    for _ in range(len(docs_to_update)):
        try:
            doc_id = next(doc_gen)[0]
            if doc_id not in docs_with_titles:
                print("call title creator, handle null summary")
                doc_summary = titles.get_doc_summary(id=doc_id)[0, "summary"]
                new_title = title_creator.invoke(paragraph=doc_summary)
            # call comment code, topic code, return df
            df, df_rep_paraphrase, df_rep_form = comments.rep_comment_analysis(
                doc_id
            )
            # call topics code, return df
            # make sure all fields are correct in df
            # update nlp table - do this with andrew
            # change comments code so that it takes in an id only,
            # runs from a function
            print(new_title)
            print(df)
            print(df_rep_form)
            print(df_rep_paraphrase)
        except StopIteration:
            print("NLP Update Completed")
            break
