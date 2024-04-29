from civiclens.data_engineering import access_api_data
from civiclens.utils.constants import REG_GOV_API_KEY


def test_is_duplicated_on_server():
    test_json = {
        "errors": [{"status": "500", "detail": "Incorrect result size"}],
    }
    assert access_api_data._is_duplicated_on_server(test_json)


def test_is_duplicated_on_server_real_data():
    # NRCS-2009-0004-0003 is known duplicated comment ID
    assert access_api_data.pull_reg_gov_data(
        REG_GOV_API_KEY,
        "comments",
        params={"filter[searchTerm]": "NRCS-2009-0004-0003"},
    )


def test_api_date_format_params_dockets():
    assert access_api_data.api_date_format_params(
        "dockets", "01-01-0001", "12-12-1212"
    ) == {
        "filter[lastModifiedDate][ge]": "01-01-0001 00:00:00",
        "filter[lastModifiedDate][le]": "12-12-1212 23:59:59",
    }


def test_api_date_format_params_NOT_dockets():
    assert access_api_data.api_date_format_params(
        "documents", "01-01-0001", "12-12-1212"
    ) == {
        "filter[postedDate][ge]": "01-01-0001",
        "filter[postedDate][le]": "12-12-1212",
    }


def test_pull_reg_gov_data():
    # get a known document
    # https://www.regulations.gov/document/CRC-2024-0073-0001

    access_api_data.pull_reg_gov_data(
        REG_GOV_API_KEY,
        "documents",
        params={"filter[searchTerm]": "CRC-2024-0073-0001"},
    )
