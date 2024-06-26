"""This is to check the status of the documents in the database.
- if the closing date has passed, the status should be updated
- if the closing date is null or in the future:
    - call the regulations.gov API to get the current status
"""
import logging
from datetime import datetime

from civiclens.collect.access_api_data import pull_reg_gov_data
from civiclens.collect.move_data_from_api_to_database import (
    connect_db_and_get_cursor,
    insert_document_into_db,
    query_register_API_and_merge_document_data,
)
from civiclens.utils.constants import REG_GOV_API_KEY


# Configure logging
logging.basicConfig(
    level=logging.INFO,  # You can change this to DEBUG for more detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("check_doc_status.log"),
        logging.StreamHandler(),
    ],
)


def get_open_docs() -> list:
    """
    Get all documents that are open in the database.

    Returns:
        open_docs (list): a list of tuples of the form (id, closing_date)
    """
    conn, cur = connect_db_and_get_cursor()
    with conn:
        cur.execute(
            "SELECT id, comment_end_date \
                    FROM regulations_document WHERE open_for_comment = %s",
            ("true",),
        )
        open_docs = cur.fetchall()
    if conn:
        cur.close()
        conn.close()

    return open_docs


def close_doc_comment(doc_id: str) -> None:
    """
    Update the status of a document in the database to closed.

    Args:
        doc_id (int): the id of the document to update

    """
    conn, cur = connect_db_and_get_cursor()
    with conn:
        cur.execute(
            "UPDATE regulations_document \
                    SET open_for_comment = %s \
                    WHERE id = %s",
            ("false", doc_id),
        )
    if conn:
        cur.close()
        conn.close()


def check_current_status(open_docs: list) -> None:
    """
    Check the closing date of each document in the database. Then:
    - if the closing date has passed, update the status to closed
    - if the closing date is in the future, call the regulations.gov API to
    get the current status

    Args:
        open_docs (list): a list of tuples of the form (id, docket_id,
            closing_date)
    """
    for id, closing_date in open_docs:
        if closing_date < datetime.now().date():
            logging.info(
                f"""Document {id} has passed its closing date.
                Closing the comment period."""
            )
            close_doc_comment(id)

        else:
            # call the regulations.gov API to get the current status
            doc_data = pull_reg_gov_data(
                REG_GOV_API_KEY, "documents", params={"filter[searchTerm]": id}
            )
            logging.info(
                f"Document {id} is still open. Checking the current status."
            )
            full_doc_info = query_register_API_and_merge_document_data(
                doc_data[0]
            )
            insert_document_into_db(full_doc_info)


if __name__ == "__main__":
    open_docs = get_open_docs()
    check_current_status(open_docs)
