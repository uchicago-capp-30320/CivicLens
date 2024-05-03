### Architecture Documentation

CivicLens is built largely on top of the regulations.gov API. In many ways, one can think of this application as a wrapper for this API designed to promote more transparency into rulemaking process and give users better abilities to search for opportunities to comment.

At a modular level the application contains:

- `/collect`: Contains library with functions to make calls to the regulations.gov API, data pipeline to run nightly chronjobs to collect newly posted data, and SQL files to create the tables that comprise our Postgres database.
- `/nlp`: Models to generate representative comments, topic modeling, and sentiment analysis. Also holds scripts to run NLP jobs upon new data intake, along with updating the results of the analysis within the database.
- `/regualtions`: Django backend hosting CivicLens. Models, views, and endpoints live here.
- `/templates`: HTML for the website's pages, along with layouts and other HTML objects (navigational bars, footers).
- `/tests`: Main testing suite for data intake, updating databases, NLP models, and helper functions.
- `/utils`: Miscellaneous collection of helper functions and constants.
- `/website`: Django project folder containing `settings.py` and other admin code.

## Data Intake and Flow
With the rulemaking and comment process maintained by regulations.gov, CivicLens relies entirely on this API for its data intake. How data is collected, stored, and processed for analysis is diagrammed below.

``` mermaid
graph LR
  A[regulations.gov API] --> |Nightly Chronjob| B[ETL];
  B --> C{Postgres Database};
  C ----> |New Comment Text| D[NLP Analysis];
  D --> C;
  C ----> |Document Data + Analysis| E[Django]
  E --> F[CivicLens.com];
```

Data is pulled nightly (via chronjob) from regulations.gov. Information on dockets, documents, and comments is collected and stored in a Postgres database (more information on fields can be found in [Models](models.md)). After metadata and comment text from the API is stored, if a sufficient number of new comments are collected a secondary job is triggered to run an NLP analysis of the comment text. This job produces representative comments, plain English document titles, and topic and sentiment analysis describing the comments. These outputs are then seperately uploaded to our database.
