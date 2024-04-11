import os

from access_api_data import pull_reg_gov_data
from constants import API_KEY

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
