import os
import requests
import xml.etree.ElementTree as ET
import psycopg2
import json
from requests.adapters import HTTPAdapter
from datetime import datetime

from access_api_data import pull_reg_gov_data
import access_api_data
from civiclens.utils import constants


def fetch_fr_document_details(fr_doc_num):
    api_endpoint = f"https://www.federalregister.gov/api/v1/documents/{fr_doc_num}.json?fields[]=full_text_xml_url"
    response = requests.get(api_endpoint)
    if response.status_code == 200:
        data = response.json()
        return data.get("full_text_xml_url")
    else:
        error_message = f"Error fetching FR document details for {fr_doc_num}: {response.status_code}"
        raise Exception(error_message)


def fetch_xml_content(url):
    """
    Fetches XML content from a given URL.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        error_message = f"Error fetching XML content from {url}: {response.status_code}"
        raise Exception(error_message)


def parse_xml_content(xml_content):
    """
    Parses XML content and extracts relevant data such as agency type, CFR, RIN, title, summary, etc.
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

    # Add more based on discussion with Backend team

    return extracted_data


def extract_xml_text_from_doc(doc):
    """
    Processes each document in the data_list, fetching and parsing its XML content.
    """
    processed_data = []

    xml_url = doc.get("Full Text XML URL")
    if xml_url:
        xml_content = fetch_xml_content(xml_url)
        if xml_content:
            extracted_data = parse_xml_content(xml_content)
            processed_data.append({**doc, **extracted_data})

    return processed_data


def connect_db_and_get_cursor():
    connection = psycopg2.connect(
        database=constants.DATABASE_NAME,
        user=constants.DATABASE_USER,
        password=constants.DATABASE_PASSWORD,
        host=constants.DATABASE_HOST,
        port=constants.DATABASE_PORT,
    )
    cursor = connection.cursor()
    return connection, cursor


def verify_database_existence(table, api_field_val, db_field="id"):
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = f"SELECT * \
                        FROM {table} \
                        WHERE {db_field} = '{api_field_val}';"
            cursor.execute(query)
            response = cursor.fetchall()

    return response != []


def get_most_recent_doc_comment_date(doc_id):
    connection, cursor = connect_db_and_get_cursor()
    with connection:
        with cursor:
            query = f"SELECT MAX(postedDate) \
                        FROM Comments \
                        WHERE commentOnDocumentId = '{doc_id}';"
            cursor.execute(query)
            response = cursor.fetchall()

    return response


def insert_docket_into_db(docket_data):

    # need to check that docket_data is in the right format

    data_for_db = json.loads(docket_data)
    attributes = data_for_db["attributes"]
    try:

        connection, cursor = connect_db_and_get_cursor()

        with connection:
            with cursor:
                cursor.execute(
                    """
                    INSERT INTO Dockets (id, docket_type, last_modified_date, agency_id, title, object_id, highlighted_content)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
    except psycopg2.Error as e:
        error_message = (
            f"Error inserting docket {attributes['objectId']} into dockets table: {e}"
        )
        print(error_message)


def query_register_API_and_merge_document_data(doc):
    """
    Attempts to pull document text via federal register API and merge with reg gov API data

    Inputs:
        doc (json): the raw json for a document from regulations.gov API

    Outputs:
        merged_doc (json): the json with fields for text from federal register API
    """

    # extract the document text using the general register API
    fr_doc_num = doc.get("attributes", {}).get("frDocNum")
    if fr_doc_num:
        try:
            xml_url = fetch_fr_document_details(fr_doc_num)
            xml_content = fetch_xml_content(xml_url)
            parsed_xml_content = parse_xml_content(xml_content)
            doc.update(parsed_xml_content)
        except:
            error_message = f"Error accessing federal register xml data {fr_doc_num}"
            raise Exception(error_message)

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
        doc.update(blank_xml_fields)

    return doc


def insert_document_into_db(document_data):
    data_for_db = json.loads(document_data)
    attributes = data_for_db["attributes"]

    try:

        connection, cursor = connect_db_and_get_cursor()

        # TODO: confirm this SQL code

        with connection:
            with cursor:
                cursor.execute(
                    """
                    INSERT INTO Documents (id, documentType, lastModifiedDate, frDocNum, withdrawn, agencyId, commentEndDate,
                                           postedDate, docTitle, docketId, subtype, commentStartDate, openForComment,
                                           objectId, fullTextXmlUrl, agencyType, CFR, RIN, title, summary,
                                           dates, furtherInformation, supplementaryInformation)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        data_for_db["id"],
                        attributes["documentType"],
                        attributes["lastModifiedDate"],
                        attributes["frDocNum"],
                        attributes["withdrawn"],
                        attributes["agencyId"],
                        attributes["commentEndDate"],
                        attributes["postedDate"],
                        attributes["title"],
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
                    ),
                )
    except psycopg2.Error as e:
        print(
            f"Error inserting document {document_data['id']} into documents table: {e}"
        )


def get_comment_text(api_key, comment_id):
    api_url = "https://api.regulations.gov/v4/comments/"
    endpoint = f"{api_url}{comment_id}?include=attachments&api_key={api_key}"
    response = requests.get(endpoint)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")


def merge_comment_text_and_data(api_key, comment_data):

    comment_text_data = get_comment_text(api_key, comment_data["id"])

    # DECISION: only track the comment data; don't include the info on comment
    # attachments which is found elsewhere in comment_text_data

    all_comment_data = {**comment_data, **comment_text_data}
    return all_comment_data


def insert_comment_into_db(comment_data):
    connection, cursor = connect_db_and_get_cursor()

    data_for_db = json.loads(comment_data)
    attributes = data_for_db["attributes"]
    comment_text_attributes = data_for_db["data"]["attributes"]

    # Map JSON attributes to corresponding table columns
    comment_id = data_for_db["id"]
    objectId = attributes.get("objectId", "")
    # commentOn = .get("commentOn", "") # what is this? comment title?
    commentOnDocumentId = comment_text_attributes.get("commentOnDocumentId", "")
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
    commentTitle = attributes.get("title", "")
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
    sql = """
    INSERT INTO PublicComments (
        id,
        objectId,
        commentOn,
        commentOnDocumentId,
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
        commentTitle,
        trackingNbr,
        withdrawn,
        reasonWithdrawn,
        zip,
        restrictReason,
        restrictReasonType,
        submitterRep,
        submitterRepAddress,
        submitterRepCityState
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    );
    """

    # Execute the SQL statement
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    comment_id,
                    objectId,
                    commentOn,
                    commentOnDocumentId,
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
                    commentTitle,
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

    except psycopg2.Error as e:
        print(f"Error inserting comment {comment_data['id']} into dockets table: {e}")


### Rough sketch of the final code process
""" 
need to check that we've gotten all documents -- could do this manually with 
the documents being put into a database, or with a while loop
"""

# get documents
doc_list = pull_reg_gov_data(
    constants.REG_GOV_API_KEY,
    "documents",
    start_date="2024-01-01",
    end_date="2024-04-11",
)

commentable_docs = []
for doc in doc_list:
    if doc["attributes"]["openForComment"]:
        if not verify_database_existence("Documents", doc["id"]):
            commentable_docs.append(doc)
            # add this doc to the documents table in the database
            full_doc_info = query_register_API_and_merge_document_data(doc)
            insert_document_into_db(full_doc_info)

for doc in commentable_docs:
    docket_id = doc["attributes"]["docketId"]
    document_id = doc["attributes"]["id"]
    if not verify_database_existence("Dockets", docket_id):
        docket_data = pull_reg_gov_data(
            constants.REG_GOV_API_KEY,
            "dockets",
            params={"filter[searchTerm]": docket_id},
        )
        # add docket_data to docket table in the database
        insert_docket_into_db(docket_data)

    # get the other documents
    docket_docs = pull_reg_gov_data(
        constants.REG_GOV_API_KEY, "documents", params={"filter[searchTerm]": docket_id}
    )

    for dock_doc in docket_docs:
        if not verify_database_existence("Documents", dock_doc["id"]):
            # add this doc to the documents table in the database
            full_doc_info = query_register_API_and_merge_document_data(doc)
            insert_document_into_db(full_doc_info)

    # get the comments, comment text, and add to db
    if not verify_database_existence("Comments", "objectId", document_id):
        comment_data = pull_reg_gov_data(
            constants.REG_GOV_API_KEY,
            "comments",
            params={"filter[searchTerm]": document_id},
        )
        # add comment data to comments table in the database
        for comment in comment_data:
            all_comment_data = merge_comment_text_and_data(
                constants.REG_GOV_API_KEY, comment
            )
            insert_comment_into_db(all_comment_data)

    else:
        # get date of most recent comment on this doc in the db
        most_recent_comment_date = get_most_recent_doc_comment_date(document_id)

        # CHECK THAT WE ARE FILTERING ON THE RIGHT FIELD FOR DATE
        comment_data = pull_reg_gov_data(
            constants.REG_GOV_API_KEY,
            "comments",
            params={
                "filter[searchTerm]": document_id,
                "filter[lastModifiedDate][ge]": most_recent_comment_date,
            },
        )

        for comment in comment_data:
            all_comment_data = merge_comment_text_and_data(
                constants.REG_GOV_API_KEY, comment
            )
            insert_comment_into_db(all_comment_data)
