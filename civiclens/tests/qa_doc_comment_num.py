import requests
import time
from civiclens.collect.move_data_from_api_to_database import connect_db_and_get_cursor
from civiclens.utils.constants import (
    REG_GOV_API_KEY,
)


def pull_list_of_doc_info() -> list[tuple[str]]:
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = f"SELECT id, object_id \
                    FROM regulations_document;"
            cursor.execute(query)
            response = cursor.fetchall()

    return response


def get_doc_api_comment_count(object_id: str) -> int:
    base_url = f"https://api.regulations.gov/v4/comments"

    params = {"filter[commentOnId]": object_id}
    headers = {
            'X-Api-Key': REG_GOV_API_KEY,
            'Content-Type': 'application/json'
        }

    response = requests.get(base_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        total_elements = data["meta"]["totalElements"]
        return total_elements

    elif response.status_code == 429:  # Rate limit exceeded
        retry_after = response.headers.get("Retry-After", None)
        wait_time = (
            int(retry_after) if retry_after and retry_after.isdigit() else 3600
        )
        print(f"Rate limit exceeded. Waiting {wait_time} seconds to retry.")
        time.sleep(wait_time)
    
    else:
        print('other error -- process failed')

def get_doc_db_comment_count(document_id: str) -> int:
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = f"SELECT COUNT(*) \
                    FROM regulations_comment
                    WHERE document_id= %s;"
            cursor.execute(query, (document_id,))
            response = cursor.fetchall()

    return response

def diff_api_to_db_comment_count(document_id: str, object_id: str) -> int:
    db_count = get_doc_db_comment_count(document_id)
    api_count = get_doc_api_comment_count(object_id)

    return api_count - db_count


def fetch_comment_count_for_doc_list(doc_list):
    """
    Fetches comments count for each document ID that is open for comments.

    Args:
        document_ids (DataFrame): DataFrame containing document IDs under the column 'Object_ID'.
                                  This can be obtained from the output of fetch_documents_by_date_ranges()
        file_output_path (str): Path to save the output csv file.

    Returns:
        None: Results are saved directly to a csv file specified by file_output_path.
    """

    results = []

    for commentId in document_ids["Object_ID"]:
        continue_fetching = True
        while continue_fetching:
            
            else:
                results.append({"id": commentId, "total_elements": "Failed to fetch"})
                continue_fetching = False

    results_df = pd.DataFrame(results)
    results_df.to_csv(file_output_path)
