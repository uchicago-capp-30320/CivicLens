import time

import polars as pl
import requests

from civiclens.collect.move_data_from_api_to_database import (
    connect_db_and_get_cursor,
)
from civiclens.utils.constants import REG_GOV_API_KEY


def pull_list_of_doc_info() -> list[tuple[str]]:
    """
    Pulls fields to find right object id for all docs in regulations_document

    Args: None

    Returns: response (list of tuples of strings): the table fields of all
        docs in regulations_document

    """
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = "SELECT id, object_id, rin \
                    FROM regulations_document \
                    WHERE comment_end_date > NOW();"
            cursor.execute(query)
            response = cursor.fetchall()

    if connection:
        cursor.close()
        connection.close()

    return response


def find_object_id(object_id, rin):
    """
    Manages known bug in the table by finding the right object id

    Args:
        object_id (str): the object id field for a row
        rin (str): the rin field for a row

    Returns:
        the field which matches the right format
    """
    if object_id is not None and object_id[:2] == "09":
        return object_id
    elif rin is not None and rin[:2] == "09":
        return rin
    else:
        return None


def get_doc_api_comment_count(object_id: str) -> int:
    """
    Pulls the comment count from the API for a given document

    Args: object_id (str): the object id for a document

    Returns: total_elements (int): the number of comments in the API for doc

    """
    base_url = "https://api.regulations.gov/v4/comments"

    params = {"filter[commentOnId]": object_id}
    headers = {"X-Api-Key": REG_GOV_API_KEY, "Content-Type": "application/json"}

    continue_fetching = True
    while continue_fetching:
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            total_elements = data["meta"]["totalElements"]
            return total_elements

        elif response.status_code == 429:  # Rate limit exceeded
            retry_after = response.headers.get("Retry-After", None)
            wait_time = (
                int(retry_after)
                if retry_after and retry_after.isdigit()
                else 3600
            )
            print(f"Rate limit exceeded. Waiting {wait_time} seconds to retry.")
            time.sleep(wait_time)

        else:
            print(
                f"API request failed with status code: {response.status_code}"
            )
            continue_fetching = False

    # Return a default value
    return 0


def get_doc_db_comment_count(document_id: str) -> int:
    """
    Get the count of number of comments on a doc in regulations_comment

    Args: document_id (str): the id of a given document

    Returns: db_count (int): the comment comment on doc in regulations_comment
    """
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = "SELECT COUNT(*) \
                    FROM regulations_comment \
                    WHERE document_id= %s;"
            cursor.execute(query, (document_id,))
            response = cursor.fetchone()

    if connection:
        cursor.close()
        connection.close()

    db_count = response[0]
    return db_count


def diff_api_to_db_comment_count(
    document_id: str, object_id: str, rin: str
) -> dict:
    """
    Take the db fields and get the comment counts (and diff) from API and db

    Args:
        document_id (str): the document_id field for a row
        object_id (str): the object id field for a row
        rin (str): the rin field for a row

    Returns:
        dict with str keys and in vals: the database count of comments, API
        count of comments, and difference between those numbers
    """
    db_count = get_doc_db_comment_count(document_id)

    real_object_id = find_object_id(object_id, rin)
    if real_object_id is None:
        diff = None
    else:
        api_count = get_doc_api_comment_count(real_object_id)
        diff = api_count - db_count

    return {"db_count": db_count, "api_count": api_count, "diff": diff}


def fetch_comment_count_for_docs_in_db():
    """
    Get the comment counts for all documents open for comment

    Args: None

    Returns: polars dataframe with columns: document_id, object_id, rin,
        db_count, api_count, diff
    """

    ret_lst = []
    doc_tup_list = pull_list_of_doc_info()
    print(f"{len(doc_tup_list)} documents in the database")
    counter = 0

    for document_id, object_id, rin in doc_tup_list:
        count_dict = diff_api_to_db_comment_count(document_id, object_id, rin)
        count_dict.update(
            {"document_id": document_id, "object_id": object_id, "rin": rin}
        )
        ret_lst.append(count_dict)

        if counter % 100 == 0:
            print(f"{counter} docs checked")
        counter += 1

    results_df = pl.DataFrame(ret_lst)
    print("finished!")

    return results_df


def main():
    df = fetch_comment_count_for_docs_in_db()
    df.write_csv("comment_num_api_and_db.csv")


if __name__ == "__main__":
    main()
