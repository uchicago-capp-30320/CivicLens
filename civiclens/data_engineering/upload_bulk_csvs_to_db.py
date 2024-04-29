import polars as pl
import json
from datetime import datetime
import argparse

from access_api_data import pull_reg_gov_data
from move_data_from_api_to_database import insert_comment_into_db
from civiclens.utils.constants import REG_GOV_API_KEY


def load_data(file_name: str) -> pl.DataFrame([]):
    """
    Loads csv file into a polars df of comments and filters out null comments
    """
    q = pl.scan_csv(file_name).filter(~pl.col("Comment").is_null())
    df = q.collect()

    return df


def get_document_objectId(doc_id):
    """ """
    doc_data = pull_reg_gov_data(
        REG_GOV_API_KEY, "documents", params={"filter[searchTerm]": doc_id}
    )

    return doc_data["attibutes"]["objectId"]


def format_date(datetime_str: str) -> str:
    """
    Format a datetime string to the desired ISO 8601 format with UTC ('Z' timezone)
    """
    try:
        # Parse the input datetime string (assuming it's in ISO 8601 format)
        parsed_datetime = datetime.fromisoformat(datetime_str)

        # Convert the parsed datetime object to the desired format string
        formatted_datetime_str = parsed_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

        return formatted_datetime_str
    except ValueError as e:
        # Handle parsing error
        print(f"Error parsing datetime string '{datetime_str}': {e}")
        return None


def extract_fields_from_row(df_row: pl.DataFrame([]), doc_objectId: str) -> dict:
    """
    Takes a polars row and outputs it in properly formatted dict

    Inputs:
        df_row (polars df): a polars row representing a comment
        doc_objectId (str): the object id for the doc the comment is on. Not included
            in the csv, but necessary to insert into the db

    Returns: comment_data (json): formatted json with fields extracted from the row,
        ready to be inserted into the comments db table
    """

    comment_data = {
        "data": {"attributes": {}},
        "attributes": {},
        "type": "comments",
    }

    attributes = comment_data["attributes"]
    comment_text_attributes = comment_data["data"]["attributes"]
    comment_data["id"] = df_row[
        "Document ID"
    ]  # this is the ID field, confusingly named
    attributes["objectId"] = doc_objectId
    comment_text_attributes["commentOn"] = None
    comment_text_attributes["commentOnDocumentId"] = df_row["Comment on Document ID"]
    comment_text_attributes["duplicateComments"] = df_row["Duplicate Comments"]
    comment_text_attributes["stateProvinceRegion"] = df_row["State/Province"]
    comment_text_attributes["subtype"] = df_row["Document Subtype"]
    comment_text_attributes["comment"] = df_row["Comment"]
    comment_text_attributes["firstName"] = df_row["First Name"]
    comment_text_attributes["lastName"] = df_row["Last Name"]
    comment_text_attributes["address1"] = None
    comment_text_attributes["address2"] = None
    comment_text_attributes["city"] = df_row["City"]
    comment_text_attributes["category"] = df_row["Category"]
    comment_text_attributes["country"] = df_row["Country"]
    comment_text_attributes["email"] = None
    comment_text_attributes["phone"] = None
    comment_text_attributes["govAgency"] = df_row["Government Agency"]
    comment_text_attributes["govAgencyType"] = df_row["Government Agency Type"]
    comment_text_attributes["organization"] = df_row["Organization Name"]
    comment_text_attributes["originalDocumentId"] = None
    comment_text_attributes["modifyDate"] = None
    comment_text_attributes["pageCount"] = (
        df_row["Page Count"] if df_row["Page Count"] else 0
    )
    comment_text_attributes["postedDate"] = format_date(df_row["Posted Date"])
    # comment_text_attributes["postedDate"] = str((df_row["Posted Date"]))
    comment_text_attributes["receiveDate"] = format_date(df_row["Received Date"])
    # comment_text_attributes["receiveDate"] = str(df_row["Received Date"])
    attributes["title"] = df_row["Title"]
    comment_text_attributes["trackingNbr"] = df_row["Tracking Number"]
    comment_text_attributes["withdrawn"] = df_row["Is Withdrawn?"]
    comment_text_attributes["reasonWithdrawn"] = df_row["Reason Withdrawn"]
    comment_text_attributes["zip"] = df_row["Zip/Postal Code"]
    comment_text_attributes["restrictReason"] = df_row["Restrict Reason"]
    comment_text_attributes["restrictReasonType"] = df_row["Restrict Reason Type"]
    comment_text_attributes["submitterRep"] = df_row["Submitter Representative"]
    comment_text_attributes["submitterRepAddress"] = df_row["Representative's Address"]
    comment_text_attributes["submitterRepCityState"] = df_row[
        "Representative's City, State & Zip"
    ]

    return comment_data


def load_bulk_comments_csv_to_db(file_name: str) -> None:
    """
    Takes a csv of bulk downloaded comments and puts them in the comments db table

    Input: file_name (str): the filepath and name of the csv file, eg,
        "~/Downloads/lve-blav-h8al.csv"

    Returns: nothing; adds the comments to the db
    """
    df = load_data(file_name)

    doc_objectId = df[0]["Comment on Document ID"].item()
    for row in df.rows(named=True):
        comment_data = extract_fields_from_row(row, doc_objectId)
        response = insert_comment_into_db(comment_data)
        if response["error"]:
            print(response["description"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload bulk download csv file of comments to db"
    )
    parser.add_argument(
        "file_name",
        type=str,
        help="File path and file name",
    )
    args = parser.parse_args()
    print("starting bulk upload")
    load_bulk_comments_csv_to_db(args.file_name)
    print("bulk upload finished")
