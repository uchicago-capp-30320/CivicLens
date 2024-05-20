from civiclens.collect import access_api_data
from unittest.mock import patch, MagicMock

api_key = "DEMO_KEY"


def test_is_duplicated_on_server():
    """
    500 status should get flagged as something duplicated
    """
    test_json = {
        "errors": [{"status": "500", "detail": "Wrong result size"}],
    }
    assert access_api_data._is_duplicated_on_server(test_json)


def test_api_date_format_params():
    """
    Ensure we return the right parameters for formatting lastModifiedDate
    """
    assert access_api_data.api_date_format_params(
        "01-01-0001", "12-12-1212"
    ) == {
        "filter[lastModifiedDate][ge]": "01-01-0001 00:00:00",
        "filter[lastModifiedDate][le]": "12-12-1212 23:59:59",
    }


# def test_api_date_format_params_NOT_dockets():
#     """
#     Ensure we return the right parameters for documents
#     """
#     assert access_api_data.api_date_format_params(
#         "documents", "01-01-0001", "12-12-1212"
#     ) == {
#         "filter[postedDate][ge]": "01-01-0001",
#         "filter[postedDate][le]": "12-12-1212",
#     }


# def test_pull_reg_gov_data():
#     # get a known document
#     # https://www.regulations.gov/document/CRC-2024-0073-0001
#     assert access_api_data.pull_reg_gov_data(
#         api_key,
#         "documents",
#         params={"filter[searchTerm]": "CRC-2024-0073-0001"},
#     )


def test_format_datetime_for_api():
    """
    Check date formatted in the right way
    """
    assert (
        access_api_data.format_datetime_for_api("2020-08-10T15:58:52Z")
        == "2020-08-10 11:58:52"
    )


@patch('access_api_data.requests.Session')
def test_pagination_handling(mock_session):
    """
    Tests if pull_reg_gov_data() handles pagination.
    """
    mock_get = MagicMock()
    mock_session.return_value = mock_session_instance = MagicMock()
    mock_session_instance.get = mock_get

    # Set up mock responses for each page
    response_page_1 = MagicMock(status_code=200, json=lambda: {
        'data': ['data1', 'data2'],
        'meta': {'hasNextPage': True}
    })
    response_page_2 = MagicMock(status_code=200, json=lambda: {
        'data': ['data3'],
        'meta': {'hasNextPage': False}
    })
    mock_get.side_effect = [response_page_1, response_page_2]

    # The function being tested:
    results = access_api_data.pull_reg_gov_data(
        api_key=api_key,
        data_type='documents',
        start_date='2024-04-15',
        end_date='2024-05-12'
    )

    # Check that:
    # 1.) function handles multiple pages
    # 2.) respects pagination indicators
    assert len(results) == 3
    # 3.) aggregates data across pages
    assert 'data1' in results
    assert 'data2' in results
    assert 'data3' in results

    # Ensure that the API endpoint was called with the expected URL and params
    expected_calls = [
        (('https://api.regulations.gov/v4/documents',), {'headers': {'X-Api-Key': 'DEMO_KEY'}, 'params': {'page[size]': 250, 'page[number]': 1, 'filter[lastModifiedDate][ge]': '2024-04-15 00:00:00', 'filter[lastModifiedDate][le]': '2024-05-12 23:59:59'}, 'verify': True}),
        (('https://api.regulations.gov/v4/documents',), {'headers': {'X-Api-Key': 'DEMO_KEY'}, 'params': {'page[size]': 250, 'page[number]': 2, 'filter[lastModifiedDate][ge]': '2024-04-15 00:00:00', 'filter[lastModifiedDate][le]': '2024-05-12 23:59:59'}, 'verify': True})
    ]
    mock_get.assert_has_calls(expected_calls, any_order=True)
