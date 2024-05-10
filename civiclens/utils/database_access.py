import os
from typing import List, Optional, Tuple

import polars as pl
import psycopg2


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
    connection,
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
