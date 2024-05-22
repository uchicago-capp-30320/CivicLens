import argparse
import datetime as dt
import json
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import psycopg2
import requests
from requests.adapters import HTTPAdapter

from civiclens.collect.access_api_data import pull_reg_gov_data
from civiclens.utils.constants import (
    DATABASE_HOST,
    DATABASE_NAME,
    DATABASE_PASSWORD,
    DATABASE_PORT,
    DATABASE_USER,
    REG_GOV_API_KEY,
)
from civiclens.utils.text import clean_text


## Configure logging
logging.basicConfig(
    level=logging.INFO,  # You can change this to DEBUG for more detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("pull_data.log"), logging.StreamHandler()],
)


def fetch_fr_document_details(fr_doc_num: str) -> str:
    """
    Retrieves xml url for document text from federal register.

    Args:
        fr_doc_num (str): the unique id (comes from regulations.gov api info)

    Returns:
        xml url (str)
    """
    api_endpoint = f"https://www.federalregister.gov/api/v1/documents/{fr_doc_num}.json?fields[]=full_text_xml_url"
    response = requests.get(api_endpoint)
    if response.status_code == 200:
        data = response.json()
        return data.get("full_text_xml_url")
    else:
        error_message = f"Error fetching FR document details for {fr_doc_num}: {response.status_code}"  # noqa: E501
        raise Exception(error_message)


def fetch_xml_content(url: str) -> str:
    """
    Fetches XML content from a given URL.

    Args:
        url (str): the xml url that we want to retrive text from

    Returns:
        response.text (str): the text
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        error_message = (
            f"Error fetching XML content from {url}: {response.status_code}"
        )
        raise Exception(error_message)


def parse_xml_content(xml_content: str) -> dict:
    """
    Parses XML content and extracts relevant data such as agency type, CFR,
    RIN, title, summary, etc.

    Args:
        xml_content (str): xml formatted text

    Returns:
        extracted_data (dict): contains key parts of the extracted text
    """
    # Convert the XML string to an ElementTree object
    root = ET.fromstring(xml_content)

    # Initialize a dictionary to hold extracted data
    extracted_data = {}

    # Extract Agency Type
    agency_type = root.find('.//AGENCY[@TYPE="S"]')
    extracted_data["agencyType"] = (
        agency_type.text if agency_type is not None else "Not Found"
    )

    # Extract CFR
    cfr = root.find(".//CFR")
    extracted_data["CFR"] = cfr.text if cfr is not None else "Not Found"

    # Extract RIN
    rin = root.find(".//RIN")
    extracted_data["RIN"] = rin.text if rin is not None else "Not Found"

    # Extract Title (Subject)
    title = root.find(".//SUBJECT")
    extracted_data["title"] = title.text if title is not None else "Not Found"

    # Extract Summary
    summary = root.find(".//SUM/P")
    extracted_data["summary"] = (
        summary.text if summary is not None else "Not Found"
    )

    # Extract DATES
    dates = root.find(".//DATES/P")
    extracted_data["dates"] = dates.text if dates is not None else "Not Found"

    # Extract Further Information
    furinf = root.find(".//FURINF/P")
    extracted_data["furtherInformation"] = (
        furinf.text if furinf is not None else "Not Found"
    )

    # Extract Supplementary Information
    supl_info_texts = []
    supl_info_elements = root.findall(".//SUPLINF/*")
    for element in supl_info_elements:
        # Assuming we want to gather all text from children tags within
        # <SUPLINF>
        if element.text is not None:
            supl_info_texts.append(element.text.strip())
        for sub_element in element:
            if sub_element.text is not None:
                supl_info_texts.append(sub_element.text.strip())

    # Join all pieces of supplementary information text into a single string
    extracted_data["supplementaryInformation"] = " ".join(supl_info_texts)

    return extracted_data


def extract_xml_text_from_doc(doc: json) -> json:
    """
    Take a document's json object, pull the xml text, add the text to the
    object

    Args:
        doc (json): the object from regulations.gov API

    Returns:
        processed_data (json): the object with added text
    """
    processed_data = []

    if not doc:
        return processed_data

    fr_doc_num = doc["attributes"]["frDocNum"]
    if fr_doc_num:
        xml_url = fetch_fr_document_details(fr_doc_num)
        xml_content = fetch_xml_content(xml_url)
        if xml_content:
            extracted_data = parse_xml_content(xml_content)
            processed_data.append(
                {**doc, **extracted_data}
            )  # merge the json objects

    return processed_data


def connect_db_and_get_cursor() -> (
    tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]
):
    """
    Connect to the CivicLens database and return the objects
    """
    connection = psycopg2.connect(
        database=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST,
        port=DATABASE_PORT,
    )
    cursor = connection.cursor()
    return connection, cursor


def verify_database_existence(
    table: str, api_field_val: str, db_field: str = "id"
) -> bool:
    """
    Confirm a row exists in a db table for a given id

    Args:
        table (str): one of the tables in the CivicLens db
        api_field_val (str): the value we're looking for in the table
        db_field (str): the field in the table where we're looking for the
        value

    Returns:
        boolean indicating the value was found
    """
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = f"SELECT * \
                    FROM {table} \
                    WHERE {db_field} = %s;"
            cursor.execute(query, (api_field_val,))
            response = cursor.fetchall()

    return bool(response)


def add_data_quality_flag(
    data_id: str, data_type: str, error_message: str
) -> None:
    """Add data to the regulations_dataqa table is qa assert statements flag

    Args:
        data_id (str): id field of the data in question
        data_type (str): whether docket, document, or comment
        error_message (Error): the error and message raised by the assert
            statement
    Returns: nothing, add a row to regulations_dataqa
    """
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            cursor.execute(
                """INSERT INTO regulations_dataqa (
                    "data_id",
                    "data_type",
                    "error_message",
                    "added_at"
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    data_id = EXCLUDED.data_id,
                    data_type = EXCLUDED.data_type,
                    error_message = EXCLUDED.error_message,
                    added_at = EXCLUDED.added_at;""",
                (data_id, data_type, str(error_message), datetime.now()),
            )
        connection.commit()
    if connection:
        connection.close()
    logging.info(f"Added data quality flag for {data_id} of type {data_type}.")


def get_most_recent_doc_comment_date(doc_id: str) -> str:
    """
    Returns the date of the most recent comment for a doc

    Args:
        doc_id (str): the regulations.gov doc id

    Returns:
        response (datetime): the most recent date
    """
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = f"""SELECT MAX("posted_date") \
                        FROM regulations_comment \
                        WHERE "document_id" = '{doc_id}';"""
            cursor.execute(query)
            response = cursor.fetchall()

    # format the text
    # it seems that the regulations.gov API returns postedDate rounded to the
    # hour
    # if we used that naively as the most recent date, we might miss some
    # comments
    # when we pull comments again. By backing up one hour, we trade off some
    # unnecessary API calls for ensuring we don't miss anything
    date_dt = response[0][0]
    one_hour_prior = date_dt - dt.timedelta(hours=1)
    most_recent_date = one_hour_prior.strftime("%Y-%m-%d %H:%M:%S")

    return most_recent_date


def clean_docket_data(docket_data: json) -> None:
    # docket_data[0]
    pass


def qa_docket_data(docket_data: json) -> None:
    """
    Run assert statements to check docket data looks right

    Args:
        docket_data (json object): the docket data from the API

    Returns: (bool) whether data is in the expected format
    """

    attributes = docket_data[0]["attributes"]
    data_for_db = docket_data[0]

    try:
        # need to check that docket_data is in the right format
        assert (
            isinstance(docket_data, list) or len(docket_data) < 1
        ), "docket data in wrong format"

        assert "attributes" in data_for_db, "'attributes' not in docket_data"

        # check the fields
        assert (
            len(data_for_db["id"]) < 255
        ), "id field longer than 255 characters"
        assert attributes["docketType"] in [
            "Rulemaking",
            "Nonrulemaking",
        ], "docketType unexpected value"
        assert (
            len(attributes["lastModifiedDate"]) == 20
            and "202" in attributes["lastModifiedDate"]
        ), "lastModifiedDate is unexpected length"
        assert attributes["agencyId"].isalpha(), "agencyId is not just letter"
        assert isinstance(attributes["title"], str), "title is not string"
        assert (
            attributes["objectId"][:2] == "0b"
        ), "objectId does not start with '0b'"
        # attributes["highlightedContent"]

    except AssertionError as e:
        id = data_for_db["id"]
        logging.error(f"AssertionError: docket {id} -- {e}")
        add_data_quality_flag(id, "docket", e)


def insert_docket_into_db(docket_data: json) -> dict:
    """
    Run assert statements to check docket data looks right

    Args:
        docket_data (json): the docket info from regulations.gov API

    Returns: nothing unless an error; adds the info into the table
    """

    data_for_db = docket_data[0]
    attributes = data_for_db["attributes"]
    try:
        connection, cursor = connect_db_and_get_cursor()

        with connection:
            with cursor:
                cursor.execute(
                    """
                    INSERT INTO regulations_docket (
                        "id",
                        "docket_type",
                        "last_modified_date",
                        "agency_id",
                        "title",
                        "object_id",
                        "highlighted_content"
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        docket_type = EXCLUDED.docket_type,
                        last_modified_date = EXCLUDED.last_modified_date,
                        agency_id = EXCLUDED.agency_id,
                        title = EXCLUDED.title,
                        object_id = EXCLUDED.object_id,
                        highlighted_content = EXCLUDED.highlighted_content;
                    """,
                    (
                        data_for_db["id"],
                        attributes["docketType"],
                        attributes["lastModifiedDate"],
                        attributes["agencyId"],
                        attributes["title"],
                        attributes["objectId"],
                        attributes["highlightedContent"],
                    ),
                )
                connection.commit()
    except Exception as e:
        error_message = f"""Error inserting docket {data_for_db["id"]}
        into dockets table: {e}"""
        logging.error(error_message)
        return {
            "error": True,
            "message": e,
            "description": error_message,
        }

    return {
        "error": False,
        "message": None,
        "description": None,
    }


def add_dockets_to_db(
    doc_list: list[dict], print_statements: bool = True
) -> None:
    """
    Add the dockets connected to a list of documents into the database

    Args:
        doc_list (list of json objects): what is returned from an API call
            for documents
        print_statements (boolean): whether to print info on progress

    """
    for doc in doc_list:
        docket_id = doc["attributes"]["docketId"]
        commentable = doc["attributes"]["openForComment"]
        # if docket not in db, add it
        if commentable and (
            not verify_database_existence("regulations_docket", docket_id)
        ):
            docket_data = pull_reg_gov_data(
                REG_GOV_API_KEY,
                "dockets",
                params={"filter[searchTerm]": docket_id},
            )

            # clean
            clean_docket_data(docket_data)

            # qa
            qa_docket_data(docket_data)

            # add docket_data to docket table in the database
            insert_response = insert_docket_into_db(docket_data)
            if insert_response["error"]:
                logging.error(insert_response["description"])
            else:
                if print_statements:
                    logging.info(f"Added docket {docket_id} to the db")


def query_register_API_and_merge_document_data(doc: json) -> json:
    """
    Attempts to pull document text via federal register API and merge with reg
    gov API data

    Args:
        doc (json): the raw json for a document from regulations.gov API

    Returns:
        merged_doc (json): the json with fields for text from federal register
            API
    """

    # extract the document text using the general register API
    fr_doc_num = doc.get("attributes", {}).get("frDocNum")
    document_id = doc["id"]
    if fr_doc_num:
        try:
            xml_url = fetch_fr_document_details(fr_doc_num)
            xml_content = fetch_xml_content(xml_url)
            parsed_xml_content = parse_xml_content(xml_content)
            doc.update(parsed_xml_content)  # merge the json objects
        except Exception:
            # if there's an error, that means we can't use the xml_url to get
            # the doc text, so we enter None for those fields
            logging.error(
                rf"""Error accessing federal register xml data for frDocNum
                {fr_doc_num},\ document id {document_id}"""
            )
            blank_xml_fields = {
                "agencyType": None,
                "CFR": None,
                "RIN": None,
                "title": None,
                "summary": None,
                "dates": None,
                "furtherInformation": None,
                "supplementaryInformation": None,
            }
            doc.update(blank_xml_fields)  # merge the json objects

    else:
        blank_xml_fields = {
            "agencyType": None,
            "CFR": None,
            "RIN": None,
            "title": None,
            "summary": None,
            "dates": None,
            "furtherInformation": None,
            "supplementaryInformation": None,
        }
        doc.update(blank_xml_fields)  # merge the json objects

    return doc


def validate_fr_doc_num(field_value):
    """
    Check the fr_doc_num field is in the right format
    """

    # this is a decision: we accept None as a value
    if field_value is None:
        return True

    if field_value == "Not Found":
        return True

    if all(char.isdigit() or char == "-" for char in field_value):
        return True

    # else
    return False


def clean_document_data(document_data: json) -> None:
    """
    Clean document data in place; run cleaning code on summary
    """
    if document_data["summary"] is not None:
        document_data["summary"] = clean_text(document_data["summary"])


def check_CFR_data(document_data: json) -> bool:
    """
    Check that the CFR field looks right
    """
    try:
        assert (
            document_data["CFR"] is None
            or document_data["CFR"] == "Not Found"
            or "CFR" in document_data["CFR"]
            or document_data["CFR"].isalpha()
        )
        return True
    except AssertionError:
        return False


def qa_document_data(document_data: json) -> True:
    """
    Run assert statements to check document data looks right

    Args:
        document_data (json object): the document data from the API

    Returns: (bool) whether data is in the expected format
    """

    attributes = document_data["attributes"]

    try:
        assert len(document_data["id"]) < 255
        assert attributes["documentType"] in [
            "Proposed Rule",
            "Other",
            "Notice",
            "Not Found",
            "Rule",
        ]
        # attributes["lastModifiedDate"]
        assert validate_fr_doc_num(
            attributes["frDocNum"]
        ), "frDocNum contains unexpected characters or is None"
        assert attributes["withdrawn"] is False, "withdrawn is True"
        # attributes["agencyId"]
        assert (
            len((attributes["commentEndDate"])) == 20
            and "202" in attributes["commentEndDate"]
        ), "commentEndDate is unexpected length"
        assert (
            len(attributes["postedDate"]) == 20
        ), "postedDate is unexpected length"
        # attributes["docketId"]
        # attributes["subtype"]
        assert (
            len(attributes["commentStartDate"]) == 20
            and "202" in attributes["commentStartDate"]
        ), "commentStartDate is expected length"
        assert attributes["openForComment"] is True, "openForComment is False"
        # attributes["objectId"]
        assert (
            "https" in document_data["links"]["self"]
        ), "'https' is not in document_data['links']['self']"
        assert (
            ".gov" in document_data["links"]["self"]
        ), "'.gov' is not in document_data['links']['self']"
        # document_data["agencyType"]
        assert check_CFR_data(document_data), "CFR is not alpha characters"
        # document_data["RIN"]
        assert isinstance(attributes["title"], str), "title is not string"
        assert document_data["summary"] is None or isinstance(
            document_data["summary"], str
        ), "summary is not string"
        # document_data["dates"]
        # document_data["furtherInformation"]
        assert document_data["supplementaryInformation"] is None or isinstance(
            document_data["supplementaryInformation"], str
        ), "supplementaryInformation is not string"

    except AssertionError as e:
        id = document_data["id"]
        logging.error(f"AssertionError: document {id} -- {e}")
        add_data_quality_flag(id, "document", e)


def insert_document_into_db(document_data: json) -> dict:
    """
    Insert the info on a document into the documents table

    Args:
        document_data (json): the document info from regulations.gov API

    Returns:
        nothing unless an error; adds the info into the table
    """
    attributes = document_data["attributes"]

    fields_to_insert = (
        document_data["id"],
        attributes["documentType"],
        attributes["lastModifiedDate"],
        attributes["frDocNum"],
        attributes["withdrawn"],
        attributes["agencyId"],
        attributes["commentEndDate"],
        attributes["postedDate"],
        attributes["docketId"],
        attributes["subtype"],
        attributes["commentStartDate"],
        attributes["openForComment"],
        attributes["objectId"],
        document_data["links"]["self"],
        document_data["agencyType"],
        document_data["CFR"],
        document_data["RIN"],
        attributes["title"],
        document_data["summary"],
        document_data["dates"],
        document_data["furtherInformation"],
        document_data["supplementaryInformation"],
    )

    # annoying quirk:
    # https://stackoverflow.com/questions/47723790/psycopg2-programmingerror-
    # column-of-relation-does-not-exist
    query = """INSERT INTO regulations_document ("id",
                            "document_type",
                            "last_modified_date",
                            "fr_doc_num",
                            "withdrawn",
                            "agency_id",
                            "comment_end_date",
                            "posted_date",
                            "docket_id",
                            "subtype",
                            "comment_start_date",
                            "open_for_comment",
                            "object_id",
                            "full_text_xml_url",
                            "agency_type",
                            "cfr",
                            "rin",
                            "title",
                            "summary",
                            "dates",
                            "further_information",
                            "supplementary_information") \
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        document_type = EXCLUDED.document_type,
                        last_modified_date = EXCLUDED.last_modified_date,
                        fr_doc_num = EXCLUDED.fr_doc_num,
                        withdrawn = EXCLUDED.withdrawn,
                        agency_id = EXCLUDED.agency_id,
                        comment_end_date = EXCLUDED.comment_end_date,
                        posted_date = EXCLUDED.posted_date,
                        docket_id = EXCLUDED.docket_id,
                        subtype = EXCLUDED.subtype,
                        comment_start_date = EXCLUDED.comment_start_date,
                        open_for_comment = EXCLUDED.open_for_comment,
                        object_id = EXCLUDED.object_id,
                        full_text_xml_url = EXCLUDED.full_text_xml_url,
                        agency_type = EXCLUDED.agency_type,
                        cfr = EXCLUDED.cfr,
                        rin = EXCLUDED.rin,
                        title = EXCLUDED.title,
                        summary = EXCLUDED.summary,
                        dates = EXCLUDED.dates,
                        further_information = EXCLUDED.further_information,
                        supplementary_information =
                        EXCLUDED.supplementary_information;"""
    try:
        connection, cursor = connect_db_and_get_cursor()
        with connection:
            with cursor:
                cursor.execute(
                    query,
                    fields_to_insert,
                )
                connection.commit()
        if connection:
            connection.close()

    except Exception as e:
        error_message = f"""Error inserting document
        {document_data['id']} into dockets table: {e}"""
        logging.error(error_message)
        return {
            "error": True,
            "message": e,
            "description": error_message,
        }

    return {
        "error": False,
        "message": None,
        "description": None,
    }


def add_documents_to_db(
    doc_list: list[dict], print_statements: bool = True
) -> None:
    """
    Add a list of document json objects into the database

    Args:
        doc_list (list of json objects): what is returned from an API call for
            documents
        print_statements (boolean): whether to print info on progress

    """
    for doc in doc_list:
        document_id = doc["id"]
        commentable = doc["attributes"]["openForComment"]
        if commentable and (
            not verify_database_existence("regulations_document", document_id)
        ):
            # add this doc to the documents table in the database
            full_doc_info = query_register_API_and_merge_document_data(doc)
            # qa step
            qa_document_data(full_doc_info)

            # clean step
            clean_document_data(full_doc_info)

            # insert step
            insert_response = insert_document_into_db(full_doc_info)
            if insert_response["error"]:
                logging.info(insert_response["description"])
                # would want to add logging here
            else:
                if print_statements:
                    logging.info(f"added document {document_id} to the db")


def get_comment_text(api_key: str, comment_id: str) -> dict:
    """
    Get the text of a comment, with retry logic to handle rate limits.

    Args:
        api_key (str): key for the regulations.gov API
        comment_id (str): the id for the comment

    Returns:
        json object for the comment text
    """
    api_url = "https://api.regulations.gov/v4/comments/"
    endpoint = f"{api_url}{comment_id}?include=attachments"

    STATUS_CODE_OVER_RATE_LIMIT = 429
    WAIT_SECONDS = 3600  # Default to 1 hour

    session = requests.Session()
    session.mount("https", HTTPAdapter(max_retries=4))

    while True:
        response = session.get(
            endpoint, headers={"X-Api-Key": api_key}, verify=True
        )

        if response.status_code == 200:
            # SUCCESS! Return the JSON of the request
            return response.json()
        elif response.status_code == STATUS_CODE_OVER_RATE_LIMIT:
            retry_after = response.headers.get("Retry-After", None)
            wait_time = (
                int(retry_after)
                if retry_after and retry_after.isdigit()
                else WAIT_SECONDS
            )
            the_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logging.info(
                f"""Rate limit exceeded at {the_time}.
                Waiting {wait_time} seconds to retry."""
            )
            time.sleep(wait_time)
        else:
            logging.info(
                f"""Failed to retrieve comment data.
                Status code: {response.status_code}"""
            )
            return None


def merge_comment_text_and_data(api_key: str, comment_data: json) -> json:
    """
    Combine comment json object with the comment text json object

    Args:
        api_key (str): key for the regulations.gov API
        comment_data (json): the json object from regulations.gov

    Returns:
        combined json object for the comment and text
    """

    comment_text_data = get_comment_text(api_key, comment_data["id"])

    # DECISION: only track the comment data; don't include the info on comment
    # attachments which is found elsewhere in comment_text_data

    all_comment_data = {**comment_data, **comment_text_data}
    return all_comment_data


def clean_comment_data(comment_data: json) -> None:
    """
    Clean comment text -- make sure dates are formatted correctly
    """

    comment_text_attributes = comment_data["data"]["attributes"]

    # format the date fields
    for date_field in ["modifyDate", "postedDate", "receiveDate"]:
        comment_text_attributes[date_field] = (
            datetime.strptime(
                comment_text_attributes[date_field], "%Y-%m-%dT%H:%M:%SZ"
            )
            if comment_text_attributes[date_field]
            else None
        )

    # clean the text
    if comment_text_attributes["comment"] is not None:
        comment_text_attributes["comment"] = clean_text(
            comment_text_attributes["comment"]
        )


def qa_comment_data(comment_data: json) -> None:
    """
    Run assert statements to check comment data looks right

    Args:
        comment_data (json object): the document data from the API

    Returns: (bool) whether data is in the expected format
    """

    attributes = comment_data["attributes"]
    comment_text_attributes = comment_data["data"]["attributes"]
    try:
        assert len(comment_data["id"]) < 255, "id is more than 255 characters"

        assert (
            attributes["objectId"][:2] == "09"
        ), "objectId does not start with '09'"
        assert (
            comment_text_attributes["commentOn"][:2] == "09"
        ), "commentOn does not start with '09'"
        # comment_data["commentOnDocumentId"]
        assert (
            comment_text_attributes["duplicateComments"] == 0
        ), "duplicateComments != 0"
        # assert comment_data["stateProvinceRegion"]
        assert comment_text_attributes[
            "subtype"
        ] is None or comment_text_attributes["subtype"] in [
            "Public Comment",
            "Comment(s)",
        ], "subtype is not an expected value"
        assert isinstance(
            comment_text_attributes["comment"], str
        ), "comment is not string"
        # comment_data["firstName"]
        # comment_data["lastName"]
        # comment_data["address1"]
        # comment_data["address2"]
        # comment_data["city"]
        # comment_data["category"]
        # comment_data["country"]
        # comment_data["email"]
        # comment_data["phone"]
        # comment_data["govAgency"]
        # comment_data["govAgencyType"]
        # comment_data["organization"]
        # comment_data["originalDocumentId"]
        assert isinstance(
            comment_text_attributes["modifyDate"], datetime
        ), "modifyDate is not datetime"
        # comment_data["pageCount"]
        assert isinstance(
            comment_text_attributes["postedDate"], datetime
        ), "postedDate is not datetime"
        assert isinstance(
            comment_text_attributes["receiveDate"], datetime
        ), "receiveDate is not datetime"
        # comment_data["trackingNbr"]
        assert (
            comment_text_attributes["withdrawn"] is False
        ), "withdrawn is not False"
        # comment_data["reasonWithdrawn"]
        # comment_data["zip"]
        # comment_data["restrictReason"]
        # comment_data["restrictReasonType"]
        # comment_data["submitterRep"]
        # comment_data["submitterRepAddress"]
        # comment_data["submitterRepCityState"]

    except AssertionError as e:
        id = comment_data["id"]
        logging.error(f"AssertionError: comment {id} -- {e}")
        add_data_quality_flag(id, "comment", e)


def insert_comment_into_db(comment_data: json) -> dict:
    """
    Insert the info on a comment into the PublicComments table

    Args:
        comment_data (json): the comment info from regulations.gov API

    Returns:
        nothing unless an error; adds the info into the table
    """
    connection, cursor = connect_db_and_get_cursor()

    attributes = comment_data["attributes"]
    comment_text_attributes = comment_data["data"]["attributes"]

    # Map JSON attributes to corresponding table columns
    comment_id = comment_data["id"]
    objectId = attributes.get("objectId", "")
    commentOn = comment_text_attributes.get("commentOn", "")
    document_id = comment_text_attributes.get("commentOnDocumentId", "")
    duplicateComments = comment_text_attributes.get("duplicateComments", 0)
    stateProvinceRegion = comment_text_attributes.get("stateProvinceRegion", "")
    subtype = comment_text_attributes.get("subtype", "")
    comment = comment_text_attributes.get("comment", "")
    firstName = comment_text_attributes.get("firstName", "")
    lastName = comment_text_attributes.get("lastName", "")
    address1 = comment_text_attributes.get("address1", "")
    address2 = comment_text_attributes.get("address2", "")
    city = comment_text_attributes.get("city", "")
    category = comment_text_attributes.get("category", "")
    country = comment_text_attributes.get("country", "")
    email = comment_text_attributes.get("email", "")
    phone = comment_text_attributes.get("phone", "")
    govAgency = comment_text_attributes.get("govAgency", "")
    govAgencyType = comment_text_attributes.get("govAgencyType", "")
    organization = comment_text_attributes.get("organization", "")
    originalDocumentId = comment_text_attributes.get("originalDocumentId", "")
    modifyDate = comment_text_attributes.get("modifyDate", "")
    pageCount = comment_text_attributes.get("pageCount", 0)
    postedDate = comment_text_attributes.get("postedDate", "")
    receiveDate = comment_text_attributes.get("receiveDate", "")
    title = attributes.get("title", "")
    trackingNbr = comment_text_attributes.get("trackingNbr", "")
    withdrawn = comment_text_attributes.get("withdrawn", False)
    reasonWithdrawn = comment_text_attributes.get("reasonWithdrawn", "")
    zip = comment_text_attributes.get("zip", "")
    restrictReason = comment_text_attributes.get("restrictReason", "")
    restrictReasonType = comment_text_attributes.get("restrictReasonType", "")
    submitterRep = comment_text_attributes.get("submitterRep", "")
    submitterRepAddress = comment_text_attributes.get("submitterRepAddress", "")
    submitterRepCityState = comment_text_attributes.get(
        "submitterRepCityState", ""
    )

    # SQL INSERT statement
    query = """
    INSERT INTO regulations_comment (
        "id",
        "object_id",
        "comment_on",
        "document_id",
        "duplicate_comments",
        "state_province_region",
        "subtype",
        "comment",
        "first_name",
        "last_name",
        "address1",
        "address2",
        "city",
        "category",
        "country",
        "email",
        "phone",
        "gov_agency",
        "gov_agency_type",
        "organization",
        "original_document_id",
        "modify_date",
        "page_count",
        "posted_date",
        "receive_date",
        "title",
        "tracking_nbr",
        "withdrawn",
        "reason_withdrawn",
        "zip",
        "restrict_reason",
        "restrict_reason_type",
        "submitter_rep",
        "submitter_rep_address",
        "submitter_rep_city_state"
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (id) DO UPDATE SET
        object_id = EXCLUDED.object_id,
        comment_on = EXCLUDED.comment_on,
        document_id = EXCLUDED.document_id,
        duplicate_comments = EXCLUDED.duplicate_comments,
        state_province_region = EXCLUDED.state_province_region,
        subtype = EXCLUDED.subtype,
        comment = EXCLUDED.comment,
        first_name = EXCLUDED.first_name,
        last_name = EXCLUDED.last_name,
        address1 = EXCLUDED.address1,
        address2 = EXCLUDED.address2,
        city = EXCLUDED.city,
        category = EXCLUDED.category,
        country = EXCLUDED.country,
        email = EXCLUDED.email,
        phone = EXCLUDED.phone,
        gov_agency = EXCLUDED.gov_agency,
        gov_agency_type = EXCLUDED.gov_agency_type,
        organization = EXCLUDED.organization,
        original_document_id = EXCLUDED.original_document_id,
        modify_date = EXCLUDED.modify_date,
        page_count = EXCLUDED.page_count,
        posted_date = EXCLUDED.posted_date,
        receive_date = EXCLUDED.receive_date,
        title = EXCLUDED.title,
        tracking_nbr = EXCLUDED.tracking_nbr,
        withdrawn = EXCLUDED.withdrawn,
        reason_withdrawn = EXCLUDED.reason_withdrawn,
        zip = EXCLUDED.zip,
        restrict_reason = EXCLUDED.restrict_reason,
        restrict_reason_type = EXCLUDED.restrict_reason_type,
        submitter_rep = EXCLUDED.submitter_rep,
        submitter_rep_address = EXCLUDED.submitter_rep_address,
        submitter_rep_city_state = EXCLUDED.submitter_rep_city_state;
    """

    # Execute the SQL statement
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    comment_id,
                    objectId,
                    commentOn,
                    document_id,
                    duplicateComments,
                    stateProvinceRegion,
                    subtype,
                    comment,
                    firstName,
                    lastName,
                    address1,
                    address2,
                    city,
                    category,
                    country,
                    email,
                    phone,
                    govAgency,
                    govAgencyType,
                    organization,
                    originalDocumentId,
                    modifyDate,
                    pageCount,
                    postedDate,
                    receiveDate,
                    title,
                    trackingNbr,
                    withdrawn,
                    reasonWithdrawn,
                    zip,
                    restrictReason,
                    restrictReasonType,
                    submitterRep,
                    submitterRepAddress,
                    submitterRepCityState,
                ),
            )
            connection.commit()
        if connection:
            connection.close()

    except Exception as e:
        error_message = f"""Error inserting comment {comment_data['id']} into
        comment table: {e}"""
        logging.error(error_message)
        return {
            "error": True,
            "message": e,
            "description": error_message,
        }

    return {
        "error": False,
        "message": None,
        "description": None,
    }


def add_comments_to_db_for_new_doc(document_object_id: str) -> None:
    """
    Add comments to the comments table for a new doc (ie, when we have just
        added the doc to the database)

    Args:
        document_object_id (str): the object id for the document we want
            comments for (comes from the document json object)

    Returns: nothing; adds comments, if available, to the db
    """
    comment_data = pull_reg_gov_data(
        REG_GOV_API_KEY,
        "comments",
        params={"filter[commentOnId]": document_object_id},
    )
    # add comment data to comments table in the database
    for comment in comment_data:
        all_comment_data = merge_comment_text_and_data(REG_GOV_API_KEY, comment)

        # clean
        clean_comment_data(all_comment_data)

        # qa
        qa_comment_data(all_comment_data)

        insert_response = insert_comment_into_db(all_comment_data)

        if insert_response["error"]:
            logging.error(insert_response["description"])


def add_comments_to_db_for_existing_doc(
    document_id: str, document_object_id: str, print_statements: bool = True
) -> None:
    """
    Gets the most recent comment in the comments table and pulls comments for
        a doc from the API since then

    Args:
        document id (str): the id for the document we want comments for (comes
            from the document json object)
        document_object_id (str): the object id for the document we want
            comments for (comes from the document json object)
        print_statements (bool): whether to print during, default is true

    Returns: nothing; adds comments, if available, to the db
    """

    # get date of most recent comment on this doc in the db
    most_recent_comment_date = get_most_recent_doc_comment_date(document_id)
    if print_statements:
        logging.info(
            f"""comments found for document {document_id}, most recent was
            {most_recent_comment_date}"""
        )

    comment_data = pull_reg_gov_data(
        REG_GOV_API_KEY,
        "comments",
        params={
            "filter[commentOnId]": document_object_id,
            "filter[lastModifiedDate][ge]": most_recent_comment_date,
        },
    )

    for comment in comment_data:
        all_comment_data = merge_comment_text_and_data(REG_GOV_API_KEY, comment)

        # if documumrnent is not in the db, add it
        document_id = all_comment_data.get("commentOnDocumentId", "")
        if not verify_database_existence(
            "regulations_document", document_id, "id"
        ):
            # call the API to get the document info
            doc_list = pull_reg_gov_data(
                REG_GOV_API_KEY,
                "documents",
                params={"filter[objectId]": document_id},
            )
            add_documents_to_db(doc_list)

        # clean
        clean_comment_data(all_comment_data)

        # qa
        qa_comment_data(all_comment_data)

        insert_response = insert_comment_into_db(all_comment_data)
        if insert_response["error"]:
            logging.error(insert_response["description"])
            # would want to add logging here


def add_comments_to_db(
    doc_list: list[dict], print_statements: bool = True
) -> None:
    """
    Add comments on a list of documents to the database

    Args:
        doc_list (list of json objects): what is returned from an API call for
            documents
        print_statements (boolean): whether to print info on progress

    """
    for doc in doc_list:
        document_id = doc["id"]
        document_object_id = doc["attributes"]["objectId"]
        commentable = doc["attributes"]["openForComment"]
        # get the comments, comment text, and add to db
        if commentable:
            if not verify_database_existence(
                "regulations_comment", document_id, "document_id"
            ):  # doc doesn't exist in the db; it's new
                if print_statements:
                    logging.info(
                        f"""no comments found in database for document
                        {document_id}"""
                    )

                add_comments_to_db_for_new_doc(document_object_id)

                if print_statements:
                    logging.info(
                        f"""tried to add comments on document
                        {document_id} to the db"""
                    )

            else:  # doc exists in db; only need to add new comments
                add_comments_to_db_for_existing_doc(
                    document_id, document_object_id, print_statements
                )


def add_comments_based_on_comment_date_range(
    start_date: str, end_date: str
) -> None:
    """
    Add comments to the comments table based on a date range of when the
    comments were posted

    Args:
        start_date (str): the date in YYYY-MM-DD format to pull data from
            (inclusive)
        end_date (str): the date in YYYY-MM-DD format to stop the data pull
            (inclusive)

    Returns: nothing; adds comments, if available, to the db
    """
    comment_data = pull_reg_gov_data(
        REG_GOV_API_KEY,
        "comments",
        start_date=start_date,
        end_date=end_date,
    )

    for comment in comment_data:
        logging.info(f"processing comment {comment['id']} ")
        all_comment_data = merge_comment_text_and_data(REG_GOV_API_KEY, comment)

        document_id = all_comment_data["data"]["attributes"].get(
            "commentOnDocumentId", ""
        )
        logging.info(f"checking {document_id} is in the db")
        if verify_database_existence(
            "regulations_document",
            document_id,
            "id",
        ):
            logging.info(
                f"{document_id} is in the db! begin processing comment"
            )
            # clean
            clean_comment_data(all_comment_data)

            # qa
            qa_comment_data(all_comment_data)

            # insert
            insert_response = insert_comment_into_db(all_comment_data)
            if insert_response["error"]:
                logging.error(insert_response["description"])
            else:
                logging.info(
                    f"added comment {all_comment_data['id']} to the db"
                )


def pull_all_api_data_for_date_range(
    start_date: str,
    end_date: str,
    pull_dockets: bool,
    pull_documents: bool,
    pull_comments: bool,
) -> None:
    """
    Pull different types of data from regulations.gov API based on date range

    Args:
        start_date (str): the date in YYYY-MM-DD format to pull data from
            (inclusive)
        end_date (str): the date in YYYY-MM-DD format to stop the data pull
            (inclusive)
        pull_dockets (boolean):

    Returns:
        None; adds data to the db
    """

    # get documents
    logging.info("getting list of documents within date range")
    doc_list = pull_reg_gov_data(
        REG_GOV_API_KEY,
        "documents",
        start_date=start_date,
        end_date=end_date,
    )
    logging.info(f"got {len(doc_list)} documents")
    logging.info("now extracting docs open for comments from that list")

    # pull the commentable docs from that list
    commentable_docs = []
    for doc in doc_list:
        docket_id = doc["attributes"]["docketId"]
        if docket_id and doc["attributes"]["openForComment"]:
            commentable_docs.append(doc)
            # can't add this doc to the db right now because docket needs to be
            # added first
            # the db needs the docket primary key first

    logging.info(f"{len(commentable_docs)} documents open for comment")

    if pull_dockets:
        logging.info(
            "getting dockets associated with the documents open for comment"
        )
        add_dockets_to_db(commentable_docs)
        logging.info("no more dockets to add to db")

    if pull_documents:
        logging.info("adding documents to the db")
        add_documents_to_db(commentable_docs)
        logging.info("no more documents to add to db")

    if pull_comments:
        logging.info("adding comments to the db")
        add_comments_based_on_comment_date_range(start_date, end_date)
        logging.info("no more comments to add to db")

    logging.info("process finished")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pull info for a date range from API"
    )
    parser.add_argument(
        "start_date",
        type=str,
        help="Start date (str) for the date range (format: YYYY-MM-DD)",
    )
    parser.add_argument(
        "end_date",
        type=str,
        help="End date (str) for the date range (format: YYYY-MM-DD)",
    )
    parser.add_argument(
        "-k",
        "--pull_dockets",
        action="store_true",
        help="Pull dockets posted during date range, add to db if not there",
    )
    parser.add_argument(
        "-d",
        "--pull_documents",
        action="store_true",
        help="Pull documents posted during date range, add to db if not there",
    )
    parser.add_argument(
        "-c",
        "--pull_comments",
        action="store_true",
        help="Pull comments posted during date range, add to db if not there",
    )

    args = parser.parse_args()
    pull_all_api_data_for_date_range(
        args.start_date,
        args.end_date,
        args.pull_dockets,
        args.pull_documents,
        args.pull_comments,
    )
