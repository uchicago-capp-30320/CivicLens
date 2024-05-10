import pytest
from unittest.mock import patch, Mock, MagicMock
from unittest import TestCase
import psycopg2
import datetime

from civiclens.collect.move_data_from_api_to_database import (
    fetch_fr_document_details,
    fetch_xml_content,
    parse_xml_content,
    extract_xml_text_from_doc,
    connect_db_and_get_cursor,
    verify_database_existence,
    get_most_recent_doc_comment_date,
)


def test_fetch_fr_document_details_success():
    """
    Check we get a url back
    """
    url = "mock_url"
    mock_response = {"full_text_xml_url": "https://example.com/your_xml_file.xml"}

    api_endpoint = f"https://www.federalregister.gov/api/v1/documents/{url}.json?fields[]=full_text_xml_url"

    with patch("requests.get") as mock_api_hit:
        mock_api_hit.return_value.json.return_value = mock_response
        mock_api_hit.return_value.status_code = 200

        result = fetch_fr_document_details(url)

        assert result == "https://example.com/your_xml_file.xml"

        mock_api_hit.assert_called_with(api_endpoint)


def test_fetch_fr_document_details_error():
    blank_fr_num = ""

    api_endpoint = f"https://www.federalregister.gov/api/v1/documents/{blank_fr_num}.json?fields[]=full_text_xml_url"

    with patch("requests.get") as mock_api_hit:
        mock_api_hit.return_value.status_code = 404

        with pytest.raises(Exception) as e:
            fetch_fr_document_details(blank_fr_num)

        assert (
            str(e.value)
            == f"Error fetching FR document details for {blank_fr_num}: 404"
        )

        mock_api_hit.assert_called_with(api_endpoint)


def test_fetch_xml_content_success():
    url = "mock_url"
    expected_text = "test text"
    mock_response = expected_text

    with patch("requests.get") as mock_api_hit:
        # Configure the mock to return the expected response
        mock_api_hit.return_value.text = mock_response
        mock_api_hit.return_value.status_code = 200

        # Call the function under test
        result = fetch_xml_content(url)

        # Assert that the function returned the expected text content
        assert result == expected_text

        # Assert that requests.get was called with the correct URL
        mock_api_hit.assert_called_with(url)


def test_fetch_xml_content_failure():
    url = "mock_url"

    with patch("requests.get") as mock_api_hit:
        # Configure the mock to return the expected response
        mock_api_hit.return_value.status_code = 404

        with pytest.raises(Exception) as e:
            fetch_xml_content(url)

        assert str(e.value) == f"Error fetching XML content from {url}: 404"

        # Assert that requests.get was called with the correct URL
        mock_api_hit.assert_called_with(url)


def test_parse_xml_content_failure():
    xml_content = ""

    with pytest.raises(Exception) as e:
        parse_xml_content(xml_content)

    # assert type(e) is "ParseError"
    assert (
        str(e)
        == "<ExceptionInfo ParseError('no element found: line 1, column 0') tblen=3>"
    )


def test_extract_xml_text_from_doc_blank():
    assert extract_xml_text_from_doc({}) == []


def test_extract_xml_text_from_doc_wrong_format():
    try:
        extract_xml_text_from_doc({"nothing": 0})
    except Exception as e:
        assert type(e) is KeyError


def test_verify_database_existence():
    with patch(
        "civiclens.collect.move_data_from_api_to_database.connect_db_and_get_cursor"
    ) as mock_connect_db:
        # Mock the cursor
        mock_cursor = MagicMock()
        mock_connect_db.return_value = (
            MagicMock(),
            mock_cursor,
        )  # Mock connection and return cursor

        # Set up test parameters
        table = "example_table"
        api_field_val = "example_value"

        # Mock the cursor.execute method
        mock_cursor.fetchall.return_value = [("result_row",)]  # Simulate a found row

        # Call the function under test
        result = verify_database_existence(table, api_field_val)

        # Normalize expected and actual query strings for comparison
        expected_query = (
            (f"SELECT * FROM {table} WHERE id = %s;").replace(" ", "").replace("\n", "")
        )
        expected_params = (api_field_val.strip(),)

        actual_call_args = mock_cursor.execute.call_args_list[
            0
        ]  # Get the first call to execute
        actual_query = actual_call_args[0][0].strip().replace(" ", "").replace("\n", "")
        actual_params = actual_call_args[0][1]

        # Assert that the cursor.execute was called with the correct query
        assert actual_query == expected_query
        assert actual_params == expected_params

        # Assert that the function returned True since a row was found
        assert result is True


def test_verify_database_existence_not_found():
    with patch(
        "civiclens.collect.move_data_from_api_to_database.connect_db_and_get_cursor"
    ) as mock_connect_db:
        # Mock the cursor
        mock_cursor = MagicMock()
        mock_connect_db.return_value = (
            MagicMock(),
            mock_cursor,
        )  # Mock connection and return cursor

        # Set up test parameters
        table = "example_table"
        api_field_val = "example_value"

        # Mock the cursor.execute method
        mock_cursor.fetchall.return_value = []  # Simulate a row not found

        # Call the function under test
        result = verify_database_existence(table, api_field_val)

        # Normalize expected and actual query strings for comparison
        expected_query = (
            (f"SELECT * FROM {table} WHERE id = %s;").replace(" ", "").replace("\n", "")
        )
        expected_params = (api_field_val.strip(),)

        actual_call_args = mock_cursor.execute.call_args_list[
            0
        ]  # Get the first call to execute
        actual_query = actual_call_args[0][0].strip().replace(" ", "").replace("\n", "")
        actual_params = actual_call_args[0][1]

        # Assert that the cursor.execute was called with the correct query
        assert actual_query == expected_query
        assert actual_params == expected_params

        # Assert that the function returned False since a row wasn't found
        assert result is False


document_mock_row = [
    (
        "ACF-2024-0001-0001",
        "Proposed Rule",
        datetime.datetime(2024, 4, 20, 1, 0, 59, tzinfo=datetime.timezone.utc),
        "2024-03373",
        False,
        "ACF",
        datetime.date(2024, 4, 24),
        datetime.date(2024, 2, 23),
        None,
        datetime.date(2024, 2, 23),
        True,
        "0900006486429539",
        "https://api.regulations.gov/v4/documents/ACF-2024-0001-0001",
        None,
        "Not Found",
        "45 CFR Part 1355",
        "RIN 0970â\x80\x93AC98",
        "Adoption and Foster Care Analysis and Reporting System (AFCARS)",
        "ACF proposes to amend the Adoption...",
        "Not Found",
        "\n                        Joe Bock, The Children's Bureau, (202) 205â\x80\x938618. Telecommunications Relay users may dial 711 first. Email inquiries to \n                        ",
        "SUPPLEMENTARY INFORMATION: text to long to include in testing",
        "ACF-2024-0001",
    )
]

comment_mock_row = [
    (
        "ACF-2024-0001-0002",
        "0900006486429d13",
        "0900006486429539",
        0,
        None,
        "Public Comment",
        "comment too long to include in testing",
        "Nadiya",
        "Littlewarrior",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        datetime.datetime(2024, 2, 23, 18, 44, 57, tzinfo=datetime.timezone.utc),
        1,
        datetime.datetime(2024, 2, 23, 5, 0, tzinfo=datetime.timezone.utc),
        datetime.datetime(2024, 2, 23, 5, 0, tzinfo=datetime.timezone.utc),
        "Comment on FR Doc # 2024-03373",
        "lsy-w3o9-tprh",
        False,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        "ACF-2024-0001-0001",
    )
]


def test_get_most_recent_doc_comment_date():
    # Mock the database cursor and connection
    with patch(
        "civiclens.collect.move_data_from_api_to_database.connect_db_and_get_cursor"
    ) as mock_connect_db:
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connect_db.return_value = (mock_connection, mock_cursor)

        # Set up test parameters
        doc_id = "test_doc_id"

        # Mock the cursor.execute method to return a predefined result
        mock_cursor.fetchall.return_value = [
            [datetime.datetime(2024, 2, 23, 5, 0, tzinfo=datetime.timezone.utc)]
        ]  # Simulate query result

        # Call the function under test
        result = get_most_recent_doc_comment_date(doc_id)

        # Assert that the cursor.execute was called with the correct query
        expected_query = (
            (
                f"""SELECT MAX("posted_date") FROM regulations_comment WHERE "document_id" = '{doc_id}';"""
            )
            .replace(" ", "")
            .replace("\n", "")
        )

        mock_cursor.execute.assert_called_once()  # Ensure execute was called

        # Check the arguments passed to the execute call
        actual_call_args = mock_cursor.execute.call_args
        actual_query = actual_call_args[0][0].strip().replace(" ", "").replace("\n", "")
        actual_params = actual_call_args[0][1] if len(actual_call_args[0]) > 1 else ()

        # Assert that the cursor.execute was called with the correct query and params
        assert actual_query == expected_query
        assert actual_params == ()

        # Assert the return value is as expected
        expected_date = "2024-02-23 04:00:00"  # Expected datetime string
        assert result == expected_date
