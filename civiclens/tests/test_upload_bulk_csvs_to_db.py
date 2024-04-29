from civiclens.data_engineering import upload_bulk_csvs_to_db


def test_get_document_objectId_fakeid():
    fake_id = "NOT REAL"
    try:
        upload_bulk_csvs_to_db.get_document_objectId(fake_id)
    except IndexError as e:
        assert str(e) == "list index out of range"
        # we get this error because the API response returns an empty list


def test_get_document_objectId_no_id():
    try:
        upload_bulk_csvs_to_db.get_document_objectId("")
    except IndexError as e:
        assert str(e) == "list index out of range"
        # we get this error because the API response returns an empty list


def test_get_document_objectId_multiple_ids():
    try:
        upload_bulk_csvs_to_db.get_document_objectId(
            ["FDA-2017-V-5183-0001", "GSA-GSA-2019-0002-0028"]
        )
    except IndexError as e:
        assert str(e) == "list index out of range"
        # we get this error because the API response returns an empty list


def test_get_document_objectId_working_id():
    assert (
        upload_bulk_csvs_to_db.get_document_objectId("FDA-2017-V-5183-0001")
        == "0900006482ab30a2"
    )


def test_format_date_no_date():
    try:
        upload_bulk_csvs_to_db.format_date("")
    except Exception as e:
        # print(e)
        assert str(e) == "Invalid isoformat string: ''"


def test_format_date_good_date():
    assert (
        upload_bulk_csvs_to_db.format_date("2024-03-06T05:00:00")
        == "2024-03-06T05:00:00Z"
    )


def test_format_date_bad_date():
    try:
        upload_bulk_csvs_to_db.format_date("2024--06T05:00:00")
    except Exception as e:
        # print(e)
        assert str(e) == "Invalid isoformat string: ''"


def test_extract_fields_from_row_no_data():
    try:
        upload_bulk_csvs_to_db.extract_fields_from_row("", "test_id")
    except Exception as e:
        assert str(e) == "string indices must be integers, not 'str'"


def test_extract_fields_from_row_good_data():
    pl_row = {
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

    assert upload_bulk_csvs_to_db.extract_fields_from_row(pl_row, "test_id") == row_json


def test_extract_fields_from_row_bad_data():
    pl_row = {
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
        upload_bulk_csvs_to_db.extract_fields_from_row(pl_row, "test_id")
    except Exception as e:
        assert str(e) == "string indices must be integers, not 'str'"
