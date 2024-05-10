import json
import sqlite3

import polars as pl
import pytest

from civiclens.utils.database_access import pull_data


with open("nlp_test_data/mock-row.json", "r") as f:
    mock_data = json.loads(f)


def test_sqlite():
    query = "SELECT 1 FROM regulations_nlpoutput"
    schema = ["numbers"]
    conn = sqlite3.connect("test.db")
    out = pull_data(conn, query, schema, return_type="list")
    assert out == [(1,)]


def test_to_df():
    query = "SELECT 1 FROM regulations_nlpoutput"
    schema = ["numbers"]
    conn = sqlite3.connect("test.db")
    out = pull_data(conn, query, schema)
    assert pl.DataFrame({"numbers": [1]}).equals(out)


def test_to_list():
    query = "SELECT 1 FROM regulations_nlpoutput"
    conn = sqlite3.connect("test.db")
    out = pull_data(conn, query, return_type="list")
    assert out == [(1,)]


def test_missing_schema():
    query = "SELECT 1 FROM regulations_nlpoutput"
    conn = sqlite3.connect("test.db")
    with pytest.raises(ValueError):
        pull_data(conn, query)


def test_bad_query():
    conn = sqlite3.connect("test.db")
    with pytest.raises(RuntimeError):
        pull_data(conn, "SELECT data FROM not_a_table", return_type="list")


def test_nlp_upload():
    conn = sqlite3.connect("test.db")
