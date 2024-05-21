**/search**

Initial search page. Provides search bar and showcases trending topics or recently uploaded documents for users to click on.

Parameters:

- topics: list of trending topics to display

Example: /search/?topics=gun_control+abortion+covid-19+healthcare

Response: HTML page with search bar and trending topics.

**/search_result**

Shows search results, ways to sort and filter results, along with search bar for user to enter new search terms.

Parameters:

- sort: by_date, by_num_comments (order number of posted comments)
- filter:
    * by_agency (eg. FDA, HUD)
    * if_comment (whether a document has comment posted to it)
    * doc_type (All, Notice, Proposed Rule, etc)

Example: /search_result/?sort=by_date&by_agency=FDA&if_comment=true&doc_type=all

Response: HTML page with search bar and search results (list of documents). Infinitive scroll container for displaying resulting documents.
