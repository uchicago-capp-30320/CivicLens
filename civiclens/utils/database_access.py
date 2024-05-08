import os

import polars as pl
import psycopg2
from typing import Optional


def pull_data(query: str, schema: Optional[list[str]] = [], return_type: str = "df") -> pl.DataFrame | list[tuple]:
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
        connection = psycopg2.connect(
            database=os.getenv("DATABASE"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            host=os.getenv("DATABASE_HOST"),
            port=os.getenv("DATABASE_PORT"),
        )

        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        raise RuntimeError(f"Error while connecting to PostgreSQL: {str(error).strip()}")

    finally:
        # Close the connection and cursor to free resources
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

    if return_type == "df":
        results = pl.DataFrame(results, schema=schema)

    return results