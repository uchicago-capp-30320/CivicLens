import json
import os
from datetime import datetime
from typing import List, Optional, Tuple

import polars as pl
import psycopg2

from civiclens.nlp.tools import RepComments


class Database:
    """
    Wrapper for CivicLens postrgres DB.
    """

    def __init__(self):
        self.conn = psycopg2.connect(
            database=os.getenv("DATABASE"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            host=os.getenv("DATABASE_HOST"),
            port=os.getenv("DATABASE_PORT"),
        )

    def cursor(self):
        return self.conn.cursor()

    def close(self):
        return self.conn.close()

    def commit(self):
        return self.conn.commit()


def pull_data(
    connection: Database,
    query: str,
    schema: Optional[List[str]] = None,
    return_type: str = "df",
) -> pl.DataFrame | List[Tuple]:
    """Takes a SQL Query and returns a polars dataframe

    Args:
        query (str): SQL Query
        schema (list[str]): list of column names for the dataframe
        return_type (str): "df" or "list"

    Returns:
        Polars df of comment data or list of comment data
    """ """"""
    if return_type == "df" and not schema:
        raise ValueError("Must input schema to return df")

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
    except (Exception, psycopg2.Error) as error:
        raise RuntimeError(
            f"Error while connecting to PostgreSQL: {str(error).strip()}"
        ) from error

    finally:
        # Close the connection and cursor to free resources
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

    if return_type == "df":
        results = pl.DataFrame(results, schema=schema)

    return results


def upload_comments(connection: Database, comments: RepComments) -> None:
    """
    Uploads comment data to database.

    Args:
        connection: Postgres client
        comments: comments to be uploaded

    Returns:
        None, uploads comments to database
    """
    query = """
    INSERT INTO regulations_nlpoutput (
            rep_comments,
            doc_plain_english_title,
            num_total_comments,
            num_unique_comments,
            num_representative_comment,
            topics,
            num_topics,
            last_updated,
            created_at,
            search_topics,
            document_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(document_id)
        DO UPDATE SET
            rep_comments = EXCLUDED.rep_comments,
            doc_plain_english_title = EXCLUDED.doc_plain_english_title,
            num_total_comments = EXCLUDED.num_total_comments,
            num_unique_comments = EXCLUDED.num_unique_comments,
            num_representative_comment = EXCLUDED.num_representative_comment,
            topics = EXCLUDED.topics,
            last_updated = EXCLUDED.last_updated,
            search_topics = EXCLUDED.search_topics
        WHERE (regulations_nlpoutput.last_updated < EXCLUDED.last_updated
                or regulations_nlpoutput.last_updated IS NULL);
            """

    values = (
        json.dumps(comments.rep_comments),
        comments.doc_plain_english_title,
        comments.num_total_comments,
        comments.num_unique_comments,
        comments.num_representative_comment,
        json.dumps(comments.topics),
        len(comments.topics),
        datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        comments.last_updated.strftime("%m/%d/%Y, %H:%M:%S"),
        ", ".join(comments.search_vector),
        comments.document_id,
    )

    try:
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()

    except Exception as e:
        print(e)

    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
