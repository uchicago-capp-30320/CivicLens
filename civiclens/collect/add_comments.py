import polars as pl
import argparse
from civiclens.collect.move_data_from_api_to_database import (
    verify_database_existence,
    add_comments_to_db_for_new_doc,
    add_comments_to_db_for_existing_doc,
)


def find_object_id(object_id, rin):
    if object_id is not None and object_id[:2] == "09":
        return object_id
    elif rin is not None and rin[:2] == "09":
        return rin
    else:
        return None


def add_comments_for_existing_docs(df):

    for row in df.rows(named=True):
        document_id = row["document_id"]
        object_id = row["object_id"]
        rin = row["rin"]

        real_object_id = find_object_id(object_id, rin)

        if real_object_id is not None:
            if not verify_database_existence(
                "regulations_comment", document_id, "document_id"
            ):  # doc doesn't exist in the db; it's new
                print(f"no comments found in database for document {document_id}")

                add_comments_to_db_for_new_doc(real_object_id)

                print(f"tried to add comments on new document {document_id} to the db")

            else:  # doc exists in db; only need to add new comments
                add_comments_to_db_for_existing_doc(document_id, real_object_id)
                print(
                    f"tried to add comments on existing document {document_id} to the db"
                )
        else:
            print(f"no usable object id found for doc {document_id}")


def main(doc_to_start=None):
    """
    This is a quick and dirty (hopefully one-time function) to add comments for
    docs that show fewer comments in the regulations_comment table than the API
    reports.

    Takes the output of qa_doc_comment_num.py, gets docs that have fewer comments
    in the table than in the API, iterates through those docs and add the comments
    """
    df = pl.read_csv("comment_num_api_and_db.csv")

    # only get rows where the db has less rows than api
    df = df.filter(df["db_count"] < df["api_count"])

    # if we know a document id where we left off, subset the df accordingly
    if doc_to_start is not None:
        df = df.with_row_index(name="my_index", offset=1)
        index_pos = df.filter(df["document_id"] == doc_to_start)["my_index"].item()
        df = df[index_pos - 1 : df.height]

    print(f"{len(df)} documents which need comments added")
    add_comments_for_existing_docs(df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Input doc in the table that we left off on"
    )
    parser.add_argument(
        "doc_to_start",
        type=str,
        help="document we left off on",
    )
    args = parser.parse_args()
    main(args.doc_to_start)
