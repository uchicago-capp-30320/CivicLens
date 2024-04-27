**/document/{str:document_id}** 

Displays plain English title, posted document title, plain english summary of proposed rule, representative comments, and metadata (posting agency, dates of comment period, number of comments). Will also display visualization of sentiment analysis of comments broken down by topic.

Parameters: None

Example: /document/ATF-2024-0001-0001

Response: HTML page displaying fixed text (title, summary). Infinite scroll displaying representative comments. D3 visual displaying sentiment analysis. 


**/document/{str:document_id}/comment**

Endpoint to allow users to post comments on a given document.

Parameters: None

Response: iFrame of regulations.gov posting form or mock-up of HTML form to submit comments for a specific document. 


