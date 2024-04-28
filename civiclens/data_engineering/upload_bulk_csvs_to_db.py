import polars as pl
import json
import argparse

from move_data_from_api_to_database import insert_comment_into_db


def load_data(file_name: str) -> pl.DataFrame([]):
    """
    Loads csv file into a polars df of comments
    """
    q = pl.scan_csv(file_name).filter(pl.col("Comment") is not None)
    df = q.collect()

    return df


def extract_fields_from_row(df_row: pl.DataFrame([])) -> json:
    """
    Takes a polars row and outputs it in properly formatted json

    Input: df_row (polars df): a polars row representing a comment

    Returns: comment_data (json): formatted json with fields extracted from the row,
        ready to be inserted into the comments db table
    """

    comment_data = {"data": {"attributes": {}}, "attributes": {}}

    attributes = comment_data["attributes"]
    comment_text_attributes = comment_data["data"]["attributes"]
    comment_data["id"] = df_row[
        "Document ID"
    ].item()  # this is the ID field, confusingly named
    attributes["objectId"] = None  # TODO
    comment_text_attributes["commentOn"] = None  # TODO
    comment_text_attributes["commentOnDocumentId"] = df_row[
        "Comment on Document ID"
    ].item()
    comment_text_attributes["duplicateComments"] = df_row["Duplicate Comments"].item()
    comment_text_attributes["stateProvinceRegion"] = df_row["State/Province"].item()
    comment_text_attributes["subtype"] = df_row["Document Subtype"].item()
    comment_text_attributes["comment"] = df_row["Comment"].item()
    comment_text_attributes["firstName"] = df_row["First Name"].item()
    comment_text_attributes["lastName"] = df_row["Last Name"].item()
    comment_text_attributes["address1"] = None  # TODO
    comment_text_attributes["address2"] = None  # TODO
    comment_text_attributes["city"] = df_row["City"].item()
    comment_text_attributes["category"] = df_row["Category"].item()
    comment_text_attributes["country"] = df_row["Country"].item()
    comment_text_attributes["email"] = None  # TODO
    comment_text_attributes["phone"] = None  # TODO
    comment_text_attributes["govAgency"] = df_row["Government Agency"].item()
    comment_text_attributes["govAgencyType"] = df_row["Government Agency Type"].item()
    comment_text_attributes["organization"] = df_row["Organization Name"].item()
    comment_text_attributes["originalDocumentId"] = None  # TODO
    comment_text_attributes["modifyDate"] = None  # TODO
    comment_text_attributes["pageCount"] = (
        df_row["Page Count"].item() if df_row["Page Count"].item() else 0
    )
    comment_text_attributes["postedDate"] = df_row["Posted Date"].item()
    comment_text_attributes["receiveDate"] = df_row["Received Date"].item()
    attributes["title"] = df_row["Title"].item()
    comment_text_attributes["trackingNbr"] = df_row["Tracking Number"].item()
    comment_text_attributes["withdrawn"] = df_row["Is Withdrawn?"].item()
    comment_text_attributes["reasonWithdrawn"] = df_row["Reason Withdrawn"].item()
    comment_text_attributes["zip"] = df_row["Zip/Postal Code"].item()
    comment_text_attributes["restrictReason"] = df_row["Restrict Reason"].item()
    comment_text_attributes["restrictReasonType"] = df_row[
        "Restrict Reason Type"
    ].item()
    comment_text_attributes["submitterRep"] = df_row["Submitter Representative"].item()
    comment_text_attributes["submitterRepAddress"] = df_row[
        "Representative's Address"
    ].item()
    comment_text_attributes["submitterRepCityState"] = df_row[
        "Representative's City, State & Zip"
    ].item()

    return json.dumps(comment_data)


def load_bulk_comments_csv_to_db(file_name: str) -> None:
    """
    Takes a csv of bulk downloaded comments and puts them in the comments db table

    Input: file_name (str): the filepath and name of the csv file

    Returns: nothing; adds the comments to the db
    """
    df = load_data(file_name)
    for row in df.iter_rows:
        comment_data = extract_fields_from_row(row)
        response = insert_comment_into_db(comment_data)
        if response["error"]:
            print(response)


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
