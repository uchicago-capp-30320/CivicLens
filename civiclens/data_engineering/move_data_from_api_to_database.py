import os
import requests
import xml.etree.ElementTree as ET

from access_api_data import pull_reg_gov_data
from constants import API_KEY

def fetch_fr_document_details(fr_doc_num):
    api_endpoint = f"https://www.federalregister.gov/api/v1/documents/{fr_doc_num}.json?fields[]=full_text_xml_url"
    response = requests.get(api_endpoint)
    if response.status_code == 200:
        data = response.json()
        return data.get('full_text_xml_url')
    else:
        print(f"Error fetching FR document details for {fr_doc_num}: {response.status_code}")
        return None
    
def fetch_xml_content(url):
    """
    Fetches XML content from a given URL.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error fetching XML content from {url}: {response.status_code}")
        return None
    

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
    extracted_data['Agency Type'] = agency_type.text if agency_type is not None else 'Not Found'

    # Extract CFR
    cfr = root.find('.//CFR')
    extracted_data['CFR'] = cfr.text if cfr is not None else 'Not Found'

    # Extract RIN
    rin = root.find('.//RIN')
    extracted_data['RIN'] = rin.text if rin is not None else 'Not Found'

    # Extract Title (Subject)
    title = root.find('.//SUBJECT')
    extracted_data['Title'] = title.text if title is not None else 'Not Found'

    # Extract Summary
    summary = root.find('.//SUM/P')
    extracted_data['Summary'] = summary.text if summary is not None else 'Not Found'

    # Extract DATES
    dates = root.find('.//DATES/P')
    extracted_data['Dates'] = dates.text if dates is not None else 'Not Found'

    # Extract Further Information
    furinf = root.find('.//FURINF/P')
    extracted_data['Further Information'] = furinf.text if furinf is not None else 'Not Found'

    # Extract Supplementary Information
    supl_info_texts = []
    supl_info_elements = root.findall('.//SUPLINF/*')
    for element in supl_info_elements:
        # Assuming we want to gather all text from children tags within <SUPLINF>
        if element.text is not None:
            supl_info_texts.append(element.text.strip())
        for sub_element in element:
            if sub_element.text is not None:
                supl_info_texts.append(sub_element.text.strip())

    # Join all pieces of supplementary information text into a single string
    extracted_data['Supplementary Information'] = " ".join(supl_info_texts)

    # Add more based on discussion with Backend team

    return extracted_data

def process_documents(doc):
    """
    Processes each document in the data_list, fetching and parsing its XML content.
    """
    processed_data = []

    xml_url = doc.get('Full Text XML URL')
    if xml_url:
        xml_content = fetch_xml_content(xml_url)
        if xml_content:
            extracted_data = parse_xml_content(xml_content)
            processed_data.append({**doc, **extracted_data})

    return processed_data

# get documents
doc_list = pull_reg_gov_data(
    API_KEY, "documents", start_date="2024-01-01", end_date="2024-04-11"
)

""" 
need to check that we've gotten all documents -- could do this manually with 
the documents being put into a database, or with a while loop
"""

commentable_docs = []
for doc in doc_list:
    if doc["openForComment"]:
        if doc["id"] not in DOCUMENTS_DATABASE:
            commentable_docs.append(doc)
            # extract the document text using the general register API

            fr_doc_num = doc.get('attributes', {}).get('frDocNum')
            if fr_doc_num:
                full_text_url = fetch_fr_document_details(fr_doc_num)
                data_list.append({'Docket ID': docket_id, 'FR Doc Number': fr_doc_num, 'Full Text XML URL': full_text_url})

            # add this doc to the documents table in the database

for doc in commentable_docs:
    docket_id = doc["docketId"]
    document_id = doc["id"]
    if docket_id not in DOCKET_DATABASE:
        docket_data = pull_reg_gov_data(
            API_KEY, "dockets", params={"filter[searchTerm]": docket_id}
        )
        # add docket_data to docket table in the database

    # get the other documents
    docket_docs = pull_reg_gov_data(
        API_KEY, "documents", params={"filter[searchTerm]": docket_id}
    )

    for doc in docket_docs:
        if doc not in DOCUMENTS_DATABASE:
            # add doc to the database

    if document_id not in COMMENTS_DATABASE:
        comment_data = pull_reg_gov_data(
            API_KEY, "comments", params={"filter[searchTerm]": document_id}
        )
        # add comment data to comments table in the database
        # potentially go one step further and get the comment text, as well

    else:
        # get date of most recent comment on this doc
        most_recent_comment_data = 0  # change this

        # CHECK THAT WE ARE FILTERING ON THE RIGHT FIELD FOR DATE
        comment_data = pull_reg_gov_data(
            API_KEY,
            "comments",
            params={
                "filter[searchTerm]": document_id,
                "filter[lastModifiedDate][ge]": most_recent_comment_data,
            },
        )

        # add comment data to comments table in the database
        # potentially go one step further and get the comment text, as well

for comment in comment_data:
    # extract the comment text
    comment_id = comment['Id']

    comment_text_data = pull_reg_gov_data(
        API_KEY, "comments", params={"filter[searchTerm]": comment_id}
    )

    # put comment_text_data into comments table 