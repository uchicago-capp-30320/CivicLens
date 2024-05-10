import json
import sqlite3
from pathlib import Path

import polars as pl
import pytest

from civiclens.nlp.tools import RepComments
from civiclens.utils.database_access import pull_data, upload_comments


BASE_DIR = Path(__file__).resolve().parent

with open(BASE_DIR / "nlp_test_data/mock-row.json", "r") as f:
    mock_data = json.load(f)

fake_id = "65cc9e17-7a50-44b9-9196-c402c62b6a15"
fake_comments = RepComments(
    document_id=mock_data["document_id"],
    rep_comments=mock_data["rep_comments"],
    doc_plain_english_title=mock_data["doc_plain_english_title"],
    num_total_comments=890,
    num_representative_comment=14,
    num_unique_comments=723,
    topics=mock_data["topics"],
    uuid=fake_id,
)


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
    upload_comments(conn, fake_comments)
    results = pull_data(
        conn, f"SELECT id FROM regulations_nlpoutput where id = '{fake_id}';"
    )
    assert results == [(fake_id,)]
