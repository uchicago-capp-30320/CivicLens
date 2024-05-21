collect
==============

Quick start guide for CivicLens' internal library for accessing data via the regulations.gov API. This library contains methods for collecting comments, dockets, and documents from regulations.gov.

## Getting Started

To collect data from regulations.gov, you'll first need an API key which you can request [here](https://open.gsa.gov/api/regulationsgov/). Once you have your key, you can add it as an Environment Variable by following the steps described under [Contributing](index.md#contributing), or you can replace `api_key` with your unique key.

## Example

Let's walk through how to collect data for the proposed rule "FR-6362-P-01 Reducing Barriers to HUD-Assisted Housing." You can read the actual rule and view comments at this [link](https://www.regulations.gov/document/HUD-2024-0031-0001). To collect data on this rule, we'll need to search by the Document ID, which we can pass into the `params` argument like this:

```python
from collect import pull_reg_gov_data, merge_comment_text_and_data

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
for comment in comment_data:
    comment_json_text.append(merge_comment_text_and_data(api_key, comment))
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
