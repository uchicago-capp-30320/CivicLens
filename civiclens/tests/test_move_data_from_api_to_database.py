import pytest
from unittest.mock import patch

from civiclens.collect import move_data_from_api_to_database


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

        result = move_data_from_api_to_database.fetch_fr_document_details(url)

        assert result == "https://example.com/your_xml_file.xml"

        mock_api_hit.assert_called_with(api_endpoint)


def test_fetch_fr_document_details_error():
    blank_fr_num = ""

    api_endpoint = f"https://www.federalregister.gov/api/v1/documents/{blank_fr_num}.json?fields[]=full_text_xml_url"

    with patch("requests.get") as mock_api_hit:
        mock_api_hit.return_value.status_code = 404

        with pytest.raises(Exception) as e:
            move_data_from_api_to_database.fetch_fr_document_details(blank_fr_num)

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
        result = move_data_from_api_to_database.fetch_xml_content(url)

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
            move_data_from_api_to_database.fetch_xml_content(url)

        assert str(e.value) == f"Error fetching XML content from {url}: 404"

        # Assert that requests.get was called with the correct URL
        mock_api_hit.assert_called_with(url)


def test_parse_xml_content_failure():
    xml_content = ""

    with pytest.raises(Exception) as e:
        move_data_from_api_to_database.parse_xml_content(xml_content)

    # assert type(e) is "ParseError"
    assert (
        str(e)
        == "<ExceptionInfo ParseError('no element found: line 1, column 0') tblen=3>"
    )


def test_extract_xml_text_from_doc_blank():
    assert move_data_from_api_to_database.extract_xml_text_from_doc({}) == []


def test_extract_xml_text_from_doc_wrong_format():
    try:
        move_data_from_api_to_database.extract_xml_text_from_doc({"nothing": 0})
    except Exception as e:
        assert type(e) is KeyError
