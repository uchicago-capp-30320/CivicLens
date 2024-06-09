import sqlite3
from pathlib import Path

import polars as pl
import pytest

from civiclens.utils.database_access import pull_data
from civiclens.utils.text import parse_html


BASE_DIR = Path(__file__).resolve().parent


def test_sqlite():
    query = "SELECT 1"
    schema = ["numbers"]
    conn = sqlite3.connect(BASE_DIR / "test.db")
    out = pull_data(conn, query, schema, return_type="list")
    assert out == [(1,)]


def test_to_df():
    query = "SELECT 1"
    schema = ["numbers"]
    conn = sqlite3.connect(BASE_DIR / "test.db")
    out = pull_data(conn, query, schema)
    assert pl.DataFrame({"numbers": [1]}).equals(out)


def test_to_list():
    query = "SELECT 1"
    conn = sqlite3.connect(BASE_DIR / "test.db")
    out = pull_data(conn, query, return_type="list")
    assert out == [(1,)]


def test_missing_schema():
    query = "SELECT 1"
    conn = sqlite3.connect(BASE_DIR / "test.db")
    with pytest.raises(ValueError):
        pull_data(conn, query)


def test_bad_query():
    conn = sqlite3.connect(BASE_DIR / "test.db")
    with pytest.raises(RuntimeError):
        pull_data(conn, "SELECT data FROM not_a_table", return_type="list")


def test_encode_string():
    dirty = "(âAOsâ)"
    clean = "(“AOs”)"
    assert parse_html(dirty) == clean


def test_remove_html_entities():
    dirty = "&quot;Family Sponsor Immigration Act of 2002,&quot;"
    clean = '"Family Sponsor Immigration Act of 2002,"'
    assert parse_html(dirty) == clean


def test_remove_html_tags():
    dirty = "This <br/>has some <b>tags<span>"
    clean = "This has some tags"
    assert parse_html(dirty) == clean


def test_other_qoute_tags():
    dirty = "ldquothe black dogrdquo"
    clean = "'the black dog'"
    assert parse_html(dirty) == clean
