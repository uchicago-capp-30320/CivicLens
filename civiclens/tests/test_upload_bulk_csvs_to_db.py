import pytest
from unittest.mock import patch
import polars as pl
from civiclens.collect import upload_bulk_csvs_to_db


def test_get_document_objectId_fakeid():
    """
    Check that inputting a bad id returns an error
    """
    fake_id = "NOT_REAL"

    mock_response = []
    with patch(
        "civiclens.collect.upload_bulk_csvs_to_db.pull_reg_gov_data"
    ) as mock_pull_reg_gov_data:
        mock_pull_reg_gov_data.return_value = mock_response

        # mocked API call
        with pytest.raises(IndexError) as e:
            upload_bulk_csvs_to_db.get_document_objectId(fake_id)

        assert str(e.value) == "list index out of range"
        # we get this error because the API response returns an empty list

        # confirm run as expected
        mock_pull_reg_gov_data.assert_called_with(
            upload_bulk_csvs_to_db.REG_GOV_API_KEY,
            "documents",
            params={"filter[searchTerm]": fake_id},
        )


def test_get_document_objectId_multiple_ids():
    """
    Check that inputting incorrectly formatted ids gives an error
    """
    multiple_ids = ("FDA-2017-V-5183-0001", "GSA-GSA-2019-0002-0028")

    mock_response = []
    with patch(
        "civiclens.collect.upload_bulk_csvs_to_db.pull_reg_gov_data"
    ) as mock_pull_reg_gov_data:
        mock_pull_reg_gov_data.return_value = mock_response

        # mocked API call
        with pytest.raises(IndexError) as e:
            upload_bulk_csvs_to_db.get_document_objectId(multiple_ids)

        assert str(e.value) == "list index out of range"
        # we get this error because the API response returns an empty list

        # confirm run as expected
        mock_pull_reg_gov_data.assert_called_with(
            upload_bulk_csvs_to_db.REG_GOV_API_KEY,
            "documents",
            params={"filter[searchTerm]": multiple_ids},
        )


def test_get_document_objectId_working_id():
    """
    Check that a correct id gives what's expected
    """
    # Define the input ID and expected output
    input_id = "FDA-2017-V-5183-0001"
    expected_output = "0900006482ab30a2"

    mock_api_call_response = "0900006482ab30a2"
    with patch(
        "civiclens.collect.upload_bulk_csvs_to_db.get_document_objectId"
    ) as mock_api_call:
        mock_api_call.return_value = mock_api_call_response

        # Call the function being tested
        result = upload_bulk_csvs_to_db.get_document_objectId(input_id)

        # Assert that the function returned the expected output
        assert result == expected_output

        # Assert that the API call function was called with the correct arguments
        mock_api_call.assert_called_once_with(input_id)


def test_format_date_no_date():
    """
    Check that inputting no date gives an error
    """
    try:
        upload_bulk_csvs_to_db.format_date("")
    except Exception as e:
        assert str(e) == "Invalid isoformat string: ''"


def test_format_date_good_date():
    """
    Check that inputting an expected date format returns the right format
    """
    assert (
        upload_bulk_csvs_to_db.format_date("2024-03-06T05:00Z")
        == "2024-03-06T05:00:00Z"
    )


def test_format_date_bad_date():
    """
    Check that inputting wrong date format returns the right format
    """
    try:
        upload_bulk_csvs_to_db.format_date("2024--06T05:00:00")
    except Exception as e:
        assert type(e) is ValueError


def test_extract_fields_from_row_no_data():
    """
    Check that extracting a field from a blank row returns an error
    """
    try:
        upload_bulk_csvs_to_db.extract_fields_from_row(pl.DataFrame({}), "test_id")
    except Exception as e:
        assert type(e) is TypeError


def test_extract_fields_from_row_good_data():
    """
    Check that inputting a correctly formatted row gives the right input
    """
    pl_row_good = {
        "Document ID": "FWS-HQ-NWRS-2022-0106-35393",
        "Agency ID": "FWS",
        "Docket ID": "FWS-HQ-NWRS-2022-0106",
        "Tracking Number": "lte-g8w2-asfu",
        "Document Type": "Public Submission",
        "Posted Date": "2024-03-06T05:00Z",
        "Is Withdrawn?": False,
        "Federal Register Number": None,
        "FR Citation": None,
        "Title": "Comment from Nowicki, Ava",
        "Comment Start Date": None,
        "Comment Due Date": None,
        "Allow Late Comments": False,
        "Comment on Document ID": "FWS-HQ-NWRS-2022-0106-35375",
        "Effective Date": None,
        "Implementation Date": None,
        "Postmark Date": None,
        "Received Date": "2024-03-05T05:00Z",
        "Author Date": None,
        "Related RIN(s)": None,
        "Authors": None,
        "CFR": None,
        "Abstract": None,
        "Legacy ID": None,
        "Media": None,
        "Document Subtype": "Comment(s)",
        "Exhibit Location": None,
        "Exhibit Type": None,
        "Additional Field 1": None,
        "Additional Field 2": None,
        "Topics": None,
        "Duplicate Comments": 1,
        "OMB/PRA Approval Number": None,
        "Page Count": 1,
        "Page Length": None,
        "Paper Width": None,
        "Special Instructions": None,
        "Source Citation": None,
        "Start End Page": None,
        "Subject": None,
        "First Name": "Ava",
        "Last Name": "Nowicki",
        "City": None,
        "State/Province": None,
        "Zip/Postal Code": None,
        "Country": "United States",
        "Organization Name": None,
        "Submitter Representative": None,
        "Representative's Address": None,
        "Representative's City, State & Zip": None,
        "Government Agency": None,
        "Government Agency Type": None,
        "Comment": "I support this proposed rule. Informing refuge managers about Indigenous Knowledge of the species they are working with will undoubtedly help to advance the care and protection that the animals on these refuges recieve. Additionally, I appreciate the enumerated requirement for refuge managers to consult with adjacent landowners and tribes to ensure that refuge activity is not encroaching upon their way of life. However, I do not support the option for refuges to aquire more land for species preservation. I believe that negotiations should be made with adjacent landowners over creating a wildlife corridor, but the default option should not be to automatically purchase new land. ",
        "Category": None,
        "Restrict Reason Type": None,
        "Restrict Reason": None,
        "Reason Withdrawn": None,
        "Content Files": None,
        "Attachment Files": None,
        "Display Properties (Name, Label, Tooltip)": "pageCount, Page Count, Number of pages In the content file",
    }

    row_json = {
        "data": {
            "attributes": {
                "commentOn": None,
                "commentOnDocumentId": "FWS-HQ-NWRS-2022-0106-35375",
                "duplicateComments": 1,
                "stateProvinceRegion": None,
                "subtype": "Comment(s)",
                "comment": "I support this proposed rule. Informing refuge managers about Indigenous Knowledge of the species they are working with will undoubtedly help to advance the care and protection that the animals on these refuges recieve. Additionally, I appreciate the enumerated requirement for refuge managers to consult with adjacent landowners and tribes to ensure that refuge activity is not encroaching upon their way of life. However, I do not support the option for refuges to aquire more land for species preservation. I believe that negotiations should be made with adjacent landowners over creating a wildlife corridor, but the default option should not be to automatically purchase new land. ",
                "firstName": "Ava",
                "lastName": "Nowicki",
                "address1": None,
                "address2": None,
                "city": None,
                "category": None,
                "country": "United States",
                "email": None,
                "phone": None,
                "govAgency": None,
                "govAgencyType": None,
                "organization": None,
                "originalDocumentId": None,
                "modifyDate": None,
                "pageCount": 1,
                "postedDate": "2024-03-06T05:00:00Z",
                "receiveDate": "2024-03-05T05:00:00Z",
                "trackingNbr": "lte-g8w2-asfu",
                "withdrawn": False,
                "reasonWithdrawn": None,
                "zip": None,
                "restrictReason": None,
                "restrictReasonType": None,
                "submitterRep": None,
                "submitterRepAddress": None,
                "submitterRepCityState": None,
            }
        },
        "attributes": {"objectId": "test_id", "title": "Comment from Nowicki, Ava"},
        "type": "comments",
        "id": "FWS-HQ-NWRS-2022-0106-35393",
    }

    assert (
        upload_bulk_csvs_to_db.extract_fields_from_row(pl_row_good, "test_id")
        == row_json
    )


def test_extract_fields_from_row_bad_data():
    """
    Check that inputting an incorrectly formatted row gives an error
    """

    pl_row_bad = {
        "Document ID": "FWS-HQ-NWRS-2022-0106-35393",
        "Agency ID": "FWS",
        "Docket ID": "FWS-HQ-NWRS-2022-0106",
        "Tracking Number": "lte-g8w2-asfu",
        "Document Type": "Public Submission",
        "Posted Date": "2024-03-06T05:00Z",
        "Is Withdrawn?": False,
        "Federal Register Number": None,
        "FR Citation": None,
    }

    try:
        upload_bulk_csvs_to_db.extract_fields_from_row(pl_row_bad, "test_id")
    except Exception as e:
        assert str(e) == "'Comment on Document ID'"
