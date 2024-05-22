collect
==============

Quick start guide for CivicLens' internal library for accessing data via the regulations.gov API. This library contains methods for collecting comments, dockets, and documents from regulations.gov.

## Getting Started

To collect data from regulations.gov, you'll first need an API key which you can request [here](https://open.gsa.gov/api/regulationsgov/). Once you have your key, you can add it as an Environment Variable by following the steps described under [Contributing](index.md#contributing), or you can replace `api_key` with your unique key.

## Example 1 - Retrieving data from one docket

Let's walk through how to collect data for the proposed rule "FR-6362-P-01 Reducing Barriers to HUD-Assisted Housing." You can read the actual rule and view comments at this [link](https://www.regulations.gov/document/HUD-2024-0031-0001). To collect data on this rule, we'll need to search by the Document ID, which we can pass into the `params` argument like this:

```python
from access_api_data import pull_reg_gov_data

api_key = "YOUR-KEY_HERE"
search_terms = {"filter[searchTerm]": "HUD-2024-0031-0001"}

doc = pull_reg_gov_data(
    api_key,
    data_type="documents",  # set the datatype to document
    params=search_terms,
)
```
Now that we've collected the metadata for the document, we can use the documents's object ID to collect all the comments posted to it.

```python
doc_object_id = doc[0]["attributes"]["objectId"]

comment_data = pull_reg_gov_data(
    api_key,
    data_type="comments",
    params={"filter[commentOnId]": doc_object_id},
)
```

Finally, we can get the text for each comment by iterating over the comment metadata and making an additional request for the text.

```python
comment_json_text = []
for commentId in comment_data[0]["attributes"]["objectId"]:
    comment_json_text.append(
        pull_reg_gov_data(
            api_key,
            data_type="comments",
            params={"filter[commentOnId]": commentId},
        )
    )
```

## Example 2 - Retrieving all comments made in the first two weeks of April 2024

In this example, we demonstrate how to gather all public comments posted within the first ten days of April 2024. 
This method can also be applied to collect documents or dockets by adjusting 'data_type'.
```python
comments_apr_01_10 = pull_reg_gov_data(
    api_key,
    data_type="comments",
    start_date="2024-05-01", 
    end_date="2024-05-10",
)
```


## Reference

::: civiclens.collect.access_api_data
    options:
        show_root_heading: true
        members:
            - pull_reg_gov_data
            - api_date_format_params

::: civiclens.collect.move_data_from_api_to_database
    options:
        show_root_heading: true

::: civiclens.collect.bulk_dl
    options:
        show_root_heading: true
