import os

import polars as pl
import psycopg2


def pull_data(query: str, schema: list[str]) -> pl.DataFrame:
    """Takes a SQL Query and returns a polars dataframe

    Args:
        query (str): SQL Query
        schema (list[str]): list of column names for the dataframe

    Returns:
        pl.DataFrame: polars df of comment data
    """ """"""
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
        print("Error while connecting to PostgreSQL", error)

    finally:
        # Close the connection and cursor to free resources
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

    df = pl.DataFrame(results, schema=schema)

    return df
