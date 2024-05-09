import os
from typing import Optional

import polars as pl
import psycopg2

from civiclens.nlp.comments import RepComments


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


def pull_data(
    connection: Database,
    query: str,
    schema: Optional[list[str]] = [],
    return_type: str = "df",
) -> pl.DataFrame | list[tuple]:
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
        print(results)
    except (Exception, psycopg2.Error) as error:
        raise RuntimeError(
            f"Error while connecting to PostgreSQL: {str(error).strip()}"
        )

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
    """
    query = """INSERT INTO (
                    "id", 
                    "rep_comments",
                    "doc_plain_english_title", 
                    "num_total_comments", 
                    "num_unique_comments", 
                    "num_representative_comment", 
                    "topics", "num_topics", 
                    "last_updated", 
                    "document_id") \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                ON CONFLICT (id) DO NOTHING;"""

    values = (
        comments.uuid,
        comments.rep_comments,
        comments.doc_plain_english_title,
        comments.num_total_comments,
        comments.num_unique_comments,
        comments.num_representative_comment,
        comments.topics,
        len(comments.topics),
        comments.last_updated,
        comments.document_id,
    )

    try:
        cursor = connection.cursor()
        cursor.execute(query, values)
        
    except Exception as e:
        return f"Upload failed, error: {e}"
