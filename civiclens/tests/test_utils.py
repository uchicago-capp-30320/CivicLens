import sqlite3

import polars as pl
import pytest

from civiclens.utils.database_access import pull_data
from civiclens.utils.text import clean_text


def test_sqlite():
    query = "SELECT 1"
    schema = ["numbers"]
    conn = sqlite3.connect("test.db")
    out = pull_data(conn, query, schema, return_type="list")
    assert out == [(1,)]


def test_to_df():
    query = "SELECT 1"
    schema = ["numbers"]
    conn = sqlite3.connect("test.db")
    out = pull_data(conn, query, schema)
    assert pl.DataFrame({"numbers": [1]}).equals(out)


def test_to_list():
    query = "SELECT 1"
    conn = sqlite3.connect("test.db")
    out = pull_data(conn, query, return_type="list")
    assert out == [(1,)]


def test_missing_schema():
    query = "SELECT 1"
    conn = sqlite3.connect("tutorial.db")
    with pytest.raises(ValueError):
        pull_data(conn, query)


def test_bad_query():
    conn = sqlite3.connect("tutorial.db")
    with pytest.raises(RuntimeError):
        pull_data(conn, "SELECT data FROM not_a_table", return_type="list")


def test_clean_string():
    dirty = "<br/> Here's some text. ndash Also more text"
    clean = "Here's some text. Also more text"
    assert clean_text(dirty) == clean


def test_clean_user_regex():
    dirty = "The cat is home"
    clean = "The dog is home"
    assert clean_text(dirty, patterns=[(r"cat", "dog")]) == clean
