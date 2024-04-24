reglib DOCS
==============

Quick start guide for CivicLens' internal library for accessing data via the Regulations.gov API. This library contains methods for collecting comments, dockets, and documents from Regulations.gov. 

## Getting Started

To collect data from Regulations.gov, you'll first need an API key which can request [here](https://open.gsa.gov/api/regulationsgov/). Once you have your key, you can add it as an Environment Variable by following the steps described under [Contributing](index.md#contributing), or you can replace `api_key` with your unique key.

## Demo 

Let's walk through how to collect data for the proposed rule "FR-6362-P-01 Reducing Barriers to HUD-Assisted Housing." You can read the actual rule and view comments at this [link](https://www.regulations.gov/document/HUD-2024-0031-0001). To collect data on this rule, we'll need to search by the Document ID, which we can pass in the `params` argument like this:

```python
import access_api_data as reglib

api_key = "YOUR-KEY_HERE"
search_terms = {"filter[searchTerm]": "HUD-2024-0031-0001"}

doc = reglib.pull_reg_gov_data(
    api_key,
    data_type="documents",  # set the datatype to document
    params=search_terms,
)
```
Now that we've collected the metadata for the document, we can use the documents's object ID to collect all the comments posted to it.

```python
doc_object_id = doc[0]["attributes"]["objectId"]

comment_data = reglib.pull_reg_gov_data(
    api_key,
    data_type="comments",
    params={"filter[commentOnId]": doc_object_id},
)
```

Finally, we get the text for each comment by iterating over the comment metadata and making an additional request for the text.

```python
comment_json_text = []
for comment in comment_data:
    comment_json_text.append(reglib.merge_comment_text_and_data(api_key, comment))
```

## Reference

::: civiclens.data_engineering.access_api_data.pull_reg_gov_data
    options:
        show_root_heading: true
        heading_level: 3

::: civiclens.data_engineering.access_api_data.get_comment_text
    options:
        show_root_heading: true
        heading_level: 3

::: civiclens.data_engineering.access_api_data.merge_comment_text_and_data
    options:
        show_root_heading: true
        heading_level: 3

::: civiclens.data_engineering.access_api_data.api_date_format_params
    options:
        show_root_heading: true
        heading_level: 3
        
