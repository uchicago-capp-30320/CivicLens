from unittest.mock import MagicMock

from civiclens.collect import access_api_data as aad


api_key = "DEMO_KEY"


def test_is_duplicated_on_server():
    """
    500 status should get flagged as something duplicated
    """
    test_json = {
        "errors": [{"status": "500", "detail": "Wrong result size"}],
    }
    assert aad._is_duplicated_on_server(test_json)


def test_api_date_format_params():
    """
    Ensure we return the right parameters for formatting lastModifiedDate
    """
    assert aad.api_date_format_params("01-01-0001", "12-12-1212") == {
        "filter[lastModifiedDate][ge]": "01-01-0001 00:00:00",
        "filter[lastModifiedDate][le]": "12-12-1212 23:59:59",
    }


# def test_api_date_format_params_NOT_dockets():
#     """
#     Ensure we return the right parameters for documents
#     """
#     assert aad.api_date_format_params(
#         "documents", "01-01-0001", "12-12-1212"
#     ) == {
#         "filter[postedDate][ge]": "01-01-0001",
#         "filter[postedDate][le]": "12-12-1212",
#     }


# def test_pull_reg_gov_data():
#     # get a known document
#     # https://www.regulations.gov/document/CRC-2024-0073-0001
#     assert aad.pull_reg_gov_data(
#         api_key,
#         "documents",
#         params={"filter[searchTerm]": "CRC-2024-0073-0001"},
#     )


def test_format_datetime_for_api():
    """
    Check date formatted in the right way
    """
    assert (
        aad.format_datetime_for_api("2020-08-10T15:58:52Z")
        == "2020-08-10 11:58:52"
    )


def test_pagination_handling():
    """
    Tests if pull_reg_gov_data() handles a few pages of pagination correctly.
    """
    mock_session = MagicMock()
    mock_get = MagicMock()
    mock_session.get = mock_get

    # Manually specify each mocked response
    responses = [
        MagicMock(
            status_code=200,
            json=lambda: {
                "data": [
                    {
                        "id": f"data{i}",
                        "attributes": {
                            "lastModifiedDate": "2024-04-15T12:00:00Z"
                        },
                    }
                    for i in range(250)
                ],
                "meta": {"hasNextPage": True},
            },
        ),
        MagicMock(
            status_code=200,
            json=lambda: {
                "data": [
                    {
                        "id": f"data{i+250}",
                        "attributes": {
                            "lastModifiedDate": "2024-04-16T12:00:00Z"
                        },
                    }
                    for i in range(250)
                ],
                "meta": {"hasNextPage": True},
            },
        ),
        MagicMock(
            status_code=200,
            json=lambda: {
                "data": [
                    {
                        "id": f"data{i+500}",
                        "attributes": {
                            "lastModifiedDate": "2024-04-17T12:00:00Z"
                        },
                    }
                    for i in range(100)
                ],
                "meta": {"hasNextPage": False},
            },
        ),
    ]

    mock_get.side_effect = responses

    # Inject mock session into your function
    aad.requests.Session = MagicMock(return_value=mock_session)

    # Run the function that handles pagination
    results = aad.pull_reg_gov_data(
        api_key="DEMO_KEY",
        data_type="documents",
        start_date="2024-04-15",
        end_date="2024-04-20",
    )

    # Check that:
    # 1.) all items have been fetched and pagination handled correctly
    assert (
        len(results) == 600
    )  # Sum of the items returned in the mocked responses
    assert mock_get.call_count == 3  # Verify the number of API calls made

    # 2.) the last call updates lastModifiedDate correctly
    last_call_params = mock_get.call_args[1]["params"]
    assert "filter[lastModifiedDate][ge]" in last_call_params
    assert (
        last_call_params["filter[lastModifiedDate][ge]"]
        == "2024-04-17T12:00:00Z"
    )
