import sqlite3

import polars as pl
import pytest

from civiclens.utils.database_access import pull_data


def test_sqlite():
    query = "SELECT 1"
    schema = ["numbers"]
    conn = sqlite3.connect("test.db")
    out = pull_data(query, schema, return_type="list", connection=conn)
    assert out == [(1,)]


def test_to_df():
    query = "SELECT 1"
    schema = ["numbers"]
    conn = sqlite3.connect("test.db")
    out = pull_data(query, schema, connection=conn)
    assert pl.DataFrame({"numbers": [1]}).equals(out)


def test_to_list():
    query = "SELECT 1"
    conn = sqlite3.connect("test.db")
    out = pull_data(query, return_type="list", connection=conn)
    assert out == [(1,)]


def test_missing_schema():
    query = "SELECT 1"
    conn = sqlite3.connect("tutorial.db")
    with pytest.raises(ValueError):
        pull_data(query, connection=conn)


def test_bad_query():
    conn = sqlite3.connect("tutorial.db")
    with pytest.raises(RuntimeError):
        pull_data(
            "SELECT data FROM not_a_table", return_type="list", connection=conn
        )
