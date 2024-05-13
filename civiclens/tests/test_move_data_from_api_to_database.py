import datetime
from unittest.mock import MagicMock, patch

import pytest

from civiclens.collect.move_data_from_api_to_database import (
    extract_xml_text_from_doc,
    fetch_fr_document_details,
    fetch_xml_content,
    get_most_recent_doc_comment_date,
    parse_xml_content,
    verify_database_existence,
)


def test_fetch_fr_document_details_success():
    """
    Check we get a url back from fetch_fr_document_details
    """
    url = "mock_url"
    mock_response = {
        "full_text_xml_url": "https://example.com/your_xml_file.xml"
    }

    api_endpoint = f"https://www.federalregister.gov/api/v1/documents/{url}.json?fields[]=full_text_xml_url"

    with patch("requests.get") as mock_api_hit:
        mock_api_hit.return_value.json.return_value = mock_response
        mock_api_hit.return_value.status_code = 200

        result = fetch_fr_document_details(url)

        assert result == "https://example.com/your_xml_file.xml"

        mock_api_hit.assert_called_with(api_endpoint)


def test_fetch_fr_document_details_error():
    """
    Check we get an error when no url is submitted to fetch_fr_document_details
    """
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
    """
    Check fetch_xml_content returns expected response
    """
    url = "mock_url"
    expected_text = "test text"
    mock_response = expected_text

    with patch("requests.get") as mock_api_hit:
        # Configure the mock to return the expected response
        mock_api_hit.return_value.text = mock_response
        mock_api_hit.return_value.status_code = 200

        result = fetch_xml_content(url)
        assert result == expected_text
        mock_api_hit.assert_called_with(url)


def test_fetch_xml_content_failure():
    """
    Check fetch_xml_content flags error when API request fails
    """
    url = "mock_url"

    with patch("requests.get") as mock_api_hit:
        # Configure the mock to return the expected response
        mock_api_hit.return_value.status_code = 404

        with pytest.raises(Exception) as e:
            fetch_xml_content(url)
        assert str(e.value) == f"Error fetching XML content from {url}: 404"
        mock_api_hit.assert_called_with(url)


def test_parse_xml_content_failure():
    """
    Check parse_xml_content fails when no xml content inputted
    """
    xml_content = ""

    with pytest.raises(Exception) as e:
        parse_xml_content(xml_content)

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
    """
    Check that verify_database_existence works and runs the right query
    """
    with patch(
        "civiclens.collect.move_data_from_api_to_database.connect_db_and_get_cursor"
    ) as mock_connect_db:
        mock_cursor = MagicMock()
        mock_connect_db.return_value = (
            MagicMock(),
            mock_cursor,
        )

        table = "example_table"
        api_field_val = "example_value"

        # Mock the cursor.execute method
        mock_cursor.fetchall.return_value = [
            ("result_row",)
        ]  # Simulate a found row

        result = verify_database_existence(table, api_field_val)

        # Need to do a lot of stripping of spaces in order for assert statements to function
        expected_query = (
            (f"SELECT * FROM {table} WHERE id = %s;")
            .replace(" ", "")
            .replace("\n", "")
        )
        expected_params = (api_field_val.strip(),)

        actual_call_args = mock_cursor.execute.call_args_list[0]
        actual_query = (
            actual_call_args[0][0].strip().replace(" ", "").replace("\n", "")
        )
        actual_params = actual_call_args[0][1]

        # Assert that the cursor.execute was called with the correct query
        assert actual_query == expected_query
        assert actual_params == expected_params

        # Assert that the function returned True since a row was found
        assert result is True


def test_verify_database_existence_not_found():
    """
    Check that verify_database_existence returns false when no row found and runs the right query
    """
    with patch(
        "civiclens.collect.move_data_from_api_to_database.connect_db_and_get_cursor"
    ) as mock_connect_db:
        mock_cursor = MagicMock()
        mock_connect_db.return_value = (
            MagicMock(),
            mock_cursor,
        )

        table = "example_table"
        api_field_val = "example_value"

        # Mock the cursor.execute method
        mock_cursor.fetchall.return_value = []  # Simulate a row not found

        result = verify_database_existence(table, api_field_val)

        # Need to do a lot of stripping of spaces in order for assert statements to function
        expected_query = (
            (f"SELECT * FROM {table} WHERE id = %s;")
            .replace(" ", "")
            .replace("\n", "")
        )
        expected_params = (api_field_val.strip(),)

        actual_call_args = mock_cursor.execute.call_args_list[0]
        actual_query = (
            actual_call_args[0][0].strip().replace(" ", "").replace("\n", "")
        )
        actual_params = actual_call_args[0][1]

        assert actual_query == expected_query
        assert actual_params == expected_params

        # Assert that the function returned False since a row wasn't found
        assert result is False


def test_get_most_recent_doc_comment_date():
    """
    Check that get_most_recent_doc_comment_date returns one hour earlier than max comment posted data
    """
    with patch(
        "civiclens.collect.move_data_from_api_to_database.connect_db_and_get_cursor"
    ) as mock_connect_db:
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connect_db.return_value = (mock_connection, mock_cursor)

        doc_id = "test_doc_id"

        mock_cursor.fetchall.return_value = [
            [datetime.datetime(2024, 2, 23, 5, 0, tzinfo=datetime.timezone.utc)]
        ]  # Simulate query result

        # Call the function under test
        result = get_most_recent_doc_comment_date(doc_id)

        expected_query = (
            (
                f"""SELECT MAX("posted_date") FROM regulations_comment WHERE "document_id" = '{doc_id}';"""
            )
            .replace(" ", "")
            .replace("\n", "")
        )

        mock_cursor.execute.assert_called_once()

        # Need to do a lot of stripping of spaces in order for assert statements to function
        actual_call_args = mock_cursor.execute.call_args
        actual_query = (
            actual_call_args[0][0].strip().replace(" ", "").replace("\n", "")
        )
        actual_params = (
            actual_call_args[0][1] if len(actual_call_args[0]) > 1 else ()
        )

        # Assert that the cursor.execute was called with the correct query and params
        assert actual_query == expected_query
        assert actual_params == ()

        # Assert the return value is as expected
        expected_date = (
            "2024-02-23 04:00:00"  # One hour prior to comment posted date
        )
        assert result == expected_date
