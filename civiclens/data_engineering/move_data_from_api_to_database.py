import requests
import xml.etree.ElementTree as ET
import psycopg2
import json
import argparse
import datetime as dt
from datetime import datetime

from access_api_data import pull_reg_gov_data
from civiclens.utils import constants


def fetch_fr_document_details(fr_doc_num: str) -> str:
    """
    Retrieves xml url for document text from federal register.

    Input: fr_doc_num (str): the unique id (comes from regulations.gov api info)

    Returns: xml url (str)
    """
    api_endpoint = f"https://www.federalregister.gov/api/v1/documents/{fr_doc_num}.json?fields[]=full_text_xml_url"
    response = requests.get(api_endpoint)
    if response.status_code == 200:
        data = response.json()
        return data.get("full_text_xml_url")
    else:
        error_message = f"Error fetching FR document details for {fr_doc_num}: {response.status_code}"
        raise Exception(error_message)


def fetch_xml_content(url: str) -> str:
    """
    Fetches XML content from a given URL.

    Input: url (str): the xml url that we want to retrive text from

    Returns: response.text (str): the text
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        error_message = f"Error fetching XML content from {url}: {response.status_code}"
        raise Exception(error_message)


def parse_xml_content(xml_content: str) -> dict:
    """
    Parses XML content and extracts relevant data such as agency type, CFR, RIN, title, summary, etc.

    Input: xml_content (str): xml formatted text

    Returns: extracted_data (dict): contains key parts of the extracted text
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
    extracted_data["summary"] = summary.text if summary is not None else "Not Found"

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
        # Assuming we want to gather all text from children tags within <SUPLINF>
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
    Take a document's json object, pull the xml text, add the text to the object

    Input: doc (json): the object from regulations.gov API

    Returns: processed_data (json): the object with added text
    """
    processed_data = []

    fr_doc_num = doc["attributes"]["frDocNum"]
    if fr_doc_num:
        xml_url = fetch_fr_document_details(fr_doc_num)
        xml_content = fetch_xml_content(xml_url)
        if xml_content:
            extracted_data = parse_xml_content(xml_content)
            processed_data.append({**doc, **extracted_data})  # merge the json objects

    return processed_data


def connect_db_and_get_cursor() -> (
    tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]
):
    """
    Connect to the CivicLens database and return the objects
    """
    connection = psycopg2.connect(
        database=constants.DATABASE_NAME,
        user=constants.DATABASE_USER,
        password=constants.DATABASE_PASSWORD,
        host=constants.DATABASE_HOST,
        port=constants.DATABASE_PORT,
    )
    cursor = connection.cursor()
    return connection, cursor


def verify_database_existence(
    table: str, api_field_val: str, db_field: str = "id"
) -> bool:
    """
    Use regulations.gov API to confirm a row exists in a db table

    Inputs:
        table (str): one of the tables in the CivicLens db
        api_field_val (str): the value we're looking for in the table
        db_field (str): the field in the table where we're looking for the value

    Returns: boolean indicating the value was found
    """
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = f"SELECT * \
                    FROM {table} \
                    WHERE {db_field} = %s;"
            cursor.execute(query, (api_field_val,))
            response = cursor.fetchall()

    return response != []


def get_most_recent_doc_comment_date(doc_id: str) -> str:
    """
    Returns the date of the most recent comment for a doc

    Input: doc_id (str): the regulations.gov doc id

    Returns: response (datetime): the most recent date
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
    # it seems that the regulations.gov API returns postedDate rounded to the hour
    # if we used that naively as the most recent date, we might miss some comments
    # when we pull comments again. By backing up one hour, we trade off some
    # unnecessary API calls for ensuring we don't miss anything
    date_dt = response[0][0]
    one_hour_prior = date_dt - dt.timedelta(hours=1)
    most_recent_date = one_hour_prior.strftime("%Y-%m-%d %H:%M:%S")

    return most_recent_date


def insert_docket_into_db(docket_data: json) -> dict:
    """
    Insert the info on a docket into the dockets table

    Input: docket_data (json): the docket info from regulations.gov API

    Returns: nothing unless an error; adds the info into the table
    """

    # need to check that docket_data is in the right format
    if not isinstance(docket_data, list) or len(docket_data) < 1:
        return {
            "error": True,
            "message": "wrong data format",
            "description": "Invalid docket data format - not a list or an empty list",
        }

    data_for_db = docket_data[0]
    if "attributes" not in data_for_db:
        return {
            "error": True,
            "message": "wrong data format",
            "description": "Invalid docket data format - no attributes json object",
        }

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
                    ON CONFLICT (id) DO NOTHING;
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
    except Exception as e:
        error_message = (
            f"Error inserting docket {attributes['objectId']} into dockets table: {e}"
        )
        # print(error_message)
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


def add_dockets_to_db(doc_list: list[json], print_statements: bool = True) -> None:
    """
    Add the dockets connected to a list of documents into the database

    Inputs:
        doc_list (list of json objects): what is returned from an API call for documents
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
                constants.REG_GOV_API_KEY,
                "dockets",
                params={"filter[searchTerm]": docket_id},
            )
            # add docket_data to docket table in the database
            insert_response = insert_docket_into_db(docket_data)
            if insert_response["error"]:
                print(insert_response["description"])
                # would want to add logging here
            else:
                if print_statements:
                    print(f"added docket {docket_id} to the db")


def query_register_API_and_merge_document_data(doc: json) -> json:
    """
    Attempts to pull document text via federal register API and merge with reg gov API data

    Input: doc (json): the raw json for a document from regulations.gov API

    Returns:
        merged_doc (json): the json with fields for text from federal register API
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
            # if there's an error, that means we can't use the xml_url to get the doc text, so we enter None for those fields
            error_message = f"Error accessing federal register xml data for frDocNum {fr_doc_num}, document id {document_id}"
            print(error_message)
            # raise Exception(error_message)
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


def insert_document_into_db(document_data: json) -> dict:
    """
    Insert the info on a document into the documents table

    Input: document_data (json): the document info from regulations.gov API

    Returns: nothing unless an error; adds the info into the table
    """
    data_for_db = document_data
    attributes = data_for_db["attributes"]

    fields_to_insert = (
        data_for_db["id"],
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
        data_for_db["links"]["self"],
        data_for_db["agencyType"],
        data_for_db["CFR"],
        data_for_db["RIN"],
        attributes["title"],
        data_for_db["summary"],
        data_for_db["dates"],
        data_for_db["furtherInformation"],
        data_for_db["supplementaryInformation"],
    )

    # annoying quirk: https://stackoverflow.com/questions/47723790/psycopg2-programmingerror-column-of-relation-does-not-exist
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
                    ON CONFLICT (id) DO NOTHING;"""
    try:
        connection, cursor = connect_db_and_get_cursor()
        with connection:
            with cursor:
                cursor.execute(
                    query,
                    fields_to_insert,
                )

    except Exception as e:
        error_message = (
            f"Error inserting document {document_data['id']} into dockets table: {e}"
        )
        # print(error_message)
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


def add_documents_to_db(doc_list: list[json], print_statements: bool = True) -> None:
    """
    Add a list of document json objects into the database

    Inputs:
        doc_list (list of json objects): what is returned from an API call for documents
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
            insert_response = insert_document_into_db(full_doc_info)
            if insert_response["error"]:
                print(insert_response["description"])
                # would want to add logging here
            else:
                if print_statements:
                    print(f"added document {document_id} to the db")


def get_comment_text(api_key: str, comment_id: str) -> json:
    """
    Get the text of a comment

    Inputs:
        api_key (str): key for the regulations.gov API
        comment_id (str): the id for the comment

    Returns: the json object for the comment text
    """
    api_url = "https://api.regulations.gov/v4/comments/"
    endpoint = f"{api_url}{comment_id}?include=attachments&api_key={api_key}"
    response = requests.get(endpoint)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve comment data. Status code: {response.status_code}")
        return None


def merge_comment_text_and_data(api_key: str, comment_data: json) -> json:
    """
    Combine comment json object with the comment text json object

    Inputs:
        api_key (str): key for the regulations.gov API
        comment_data (json): the json object from regulations.gov

    Returns: the combined json object for the comment and text
    """

    comment_text_data = get_comment_text(api_key, comment_data["id"])

    # DECISION: only track the comment data; don't include the info on comment
    # attachments which is found elsewhere in comment_text_data

    all_comment_data = {**comment_data, **comment_text_data}
    return all_comment_data


def insert_comment_into_db(comment_data: json) -> dict:
    """
    Insert the info on a comment into the PublicComments table

    Input: comment_data (json): the comment info from regulations.gov API

    Returns: nothing unless an error; adds the info into the table
    """
    connection, cursor = connect_db_and_get_cursor()

    data_for_db = comment_data
    attributes = data_for_db["attributes"]
    comment_text_attributes = data_for_db["data"]["attributes"]

    # Map JSON attributes to corresponding table columns
    comment_id = data_for_db["id"]
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
    modifyDate = (
        datetime.strptime(modifyDate, "%Y-%m-%dT%H:%M:%SZ") if modifyDate else None
    )
    pageCount = comment_text_attributes.get("pageCount", 0)
    postedDate = comment_text_attributes.get("postedDate", "")
    postedDate = (
        datetime.strptime(postedDate, "%Y-%m-%dT%H:%M:%SZ") if postedDate else None
    )
    receiveDate = comment_text_attributes.get("receiveDate", "")
    receiveDate = (
        datetime.strptime(receiveDate, "%Y-%m-%dT%H:%M:%SZ") if receiveDate else None
    )
    title = attributes.get("title", "")
    trackingNbr = comment_text_attributes.get("trackingNbr", "")
    withdrawn = comment_text_attributes.get("withdrawn", False)
    reasonWithdrawn = comment_text_attributes.get("reasonWithdrawn", "")
    zip = comment_text_attributes.get("zip", "")
    restrictReason = comment_text_attributes.get("restrictReason", "")
    restrictReasonType = comment_text_attributes.get("restrictReasonType", "")
    submitterRep = comment_text_attributes.get("submitterRep", "")
    submitterRepAddress = comment_text_attributes.get("submitterRepAddress", "")
    submitterRepCityState = comment_text_attributes.get("submitterRepCityState", "")

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
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (id) DO NOTHING;
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

    except Exception as e:
        error_message = (
            f"Error inserting docket {comment_data['id']} into comment table: {e}"
        )
        # print(error_message)
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


def add_comments_to_db(doc_list: list[json], print_statements: bool = True) -> None:
    """
    Add comments on a list of documents to the database

    Inputs:
        doc_list (list of json objects): what is returned from an API call for documents
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
            ):
                if print_statements:
                    print(f"no comments found in database for document {document_id}")
                comment_data = pull_reg_gov_data(
                    constants.REG_GOV_API_KEY,
                    "comments",
                    params={"filter[commentOnId]": document_object_id},
                )
                # add comment data to comments table in the database
                for comment in comment_data:
                    all_comment_data = merge_comment_text_and_data(
                        constants.REG_GOV_API_KEY, comment
                    )
                    insert_response = insert_comment_into_db(all_comment_data)

                    if insert_response["error"]:
                        print(insert_response["description"])
                        # would want to add logging here

                if print_statements:
                    print(f"tried to add comments on document {document_id} to the db")

            else:
                # get date of most recent comment on this doc in the db
                most_recent_comment_date = get_most_recent_doc_comment_date(document_id)
                if print_statements:
                    print(
                        f"comments found for document {document_id}, most recent was {most_recent_comment_date}"
                    )

                comment_data = pull_reg_gov_data(
                    constants.REG_GOV_API_KEY,
                    "comments",
                    params={
                        "filter[commentOnId]": document_object_id,
                        "filter[lastModifiedDate][ge]": most_recent_comment_date,
                    },
                )

                for comment in comment_data:
                    all_comment_data = merge_comment_text_and_data(
                        constants.REG_GOV_API_KEY, comment
                    )
                    insert_response = insert_comment_into_db(all_comment_data)
                    if insert_response["error"]:
                        print(insert_response["description"])
                        # would want to add logging here


def pull_all_api_data_for_date_range(
    start_date: str,
    end_date: str,
    pull_dockets: bool,
    pull_documents: bool,
    pull_comments: bool,
) -> None:
    """
    Pull different types of data from regulations.gov API based on date range

    Inputs:
        start_date (str): the date in YYYY-MM-DD format to pull data from (inclusive)
        end_date (str): the date in YYYY-MM-DD format to stop the data pull (inclusive)
        pull_dockets (boolean):

    Returns: nothing; adds data to the db
    """

    # get documents
    print("getting list of documents within date range")
    doc_list = pull_reg_gov_data(
        constants.REG_GOV_API_KEY,
        "documents",
        start_date=start_date,
        end_date=end_date,
    )
    print(f"got {len(doc_list)} documents")
    print("now extracting docs open for comments from that list")

    # pull the commentable docs from that list
    commentable_docs = []
    for doc in doc_list:
        docket_id = doc["attributes"]["docketId"]
        if docket_id and doc["attributes"]["openForComment"]:
            commentable_docs.append(doc)
            # can't add this doc to the db right now because docket needs to be added first
            # the db needs the docket primary key first

    print(f"{len(commentable_docs)} documents open for comment")

    if pull_dockets:
        print("getting dockets associated with the documents open for comment")
        add_dockets_to_db(commentable_docs)
        print("no more dockets to add to db")

    if pull_documents:
        print("adding documents to the db")
        add_documents_to_db(commentable_docs)
        print("no more documents to add to db")

    if pull_comments:
        print("adding comments to the db")
        add_comments_to_db(commentable_docs)
        print("no more comments to add to db")

    print("process finished")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull info for a date range from API")
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
        help="Pull dockets for date range and add to db if not there",
    )
    parser.add_argument(
        "-d",
        "--pull_documents",
        action="store_true",
        help="Pull documents for date range and add to db if not there",
    )
    parser.add_argument(
        "-c",
        "--pull_comments",
        action="store_true",
        help="Pull comments for date range and add to db if not there",
    )

    args = parser.parse_args()
    pull_all_api_data_for_date_range(
        args.start_date,
        args.end_date,
        args.pull_dockets,
        args.pull_documents,
        args.pull_comments,
    )
