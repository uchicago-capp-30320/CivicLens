import time

import polars as pl
import requests

from civiclens.collect.move_data_from_api_to_database import (
    connect_db_and_get_cursor,
)
from civiclens.utils.constants import REG_GOV_API_KEY


def pull_list_of_doc_info() -> list[tuple[str]]:
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = "SELECT id, object_id, rin \
                    FROM regulations_document \
                    WHERE open_for_comment = True;"
            cursor.execute(query)
            response = cursor.fetchall()

    return response


def find_object_id(object_id, rin):
    if object_id is not None and object_id[:2] == "09":
        return object_id
    elif rin is not None and rin[:2] == "09":
        return rin
    else:
        return None


def get_doc_api_comment_count(object_id: str) -> int:
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
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = "SELECT COUNT(*) \
                    FROM regulations_comment \
                    WHERE document_id= %s;"
            cursor.execute(query, (document_id,))
            response = cursor.fetchone()

    db_count = response[0]
    return db_count


def diff_api_to_db_comment_count(
    document_id: str, object_id: str, rin: str
) -> dict:
    db_count = get_doc_db_comment_count(document_id)

    real_object_id = find_object_id(object_id, rin)
    if real_object_id is None:
        diff = None
    else:
        api_count = get_doc_api_comment_count(real_object_id)
        diff = api_count - db_count

    return {"db_count": db_count, "api_count": api_count, "diff": diff}


def fetch_comment_count_for_docs_in_db():
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

        # END EARLY FOR TESTING
        # if counter == 100:
        #     results_df = pl.DataFrame(ret_lst)
        #     return results_df

        if counter % 100 == 0:
            print(f"{counter} docs checked")
        counter += 1

    results_df = pl.DataFrame(ret_lst)

    return results_df


def main():
    df = fetch_comment_count_for_docs_in_db()
    df.write_csv("comment_num_api_and_db.csv")
