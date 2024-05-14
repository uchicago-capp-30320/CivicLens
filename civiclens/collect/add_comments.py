import polars as pl
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
    print(f"{len(df)} documents which need comments added")

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

                print(f"tried to add comments on document {document_id} to the db")

            else:  # doc exists in db; only need to add new comments
                add_comments_to_db_for_existing_doc(document_id, real_object_id)
        else:
            print(f"no usable object id found for doc {document_id}")


def main():
    df = pl.read_csv("comment_num_api_and_db.csv")
    filtered_df = df.filter(df["db_count"] < df["api_count"])
    add_comments_for_existing_docs(filtered_df)


if __name__ == "__main__":
    main()
