# from civiclens.utils.database_access import pull_data
# import polars as pl
# import pytest

# test_query = "SELECT 1"
# test_schema = ["numbers"]

# def test_to_df():
#     out = pull_data(test_query, test_schema)
#     assert isinstance(out, pl.DataFrame)

# def test_to_list():
#     out = pull_data(test_query, return_type="list")
#     assert isinstance(out, list)

# def test_missing_schema():
#     with pytest.raises(ValueError):
#         pull_data(test_query)

# def test_bad_query():
#     with pytest.raises(RuntimeError):
#         pull_data("SELECT data FROM not_a_table", return_type="list")
