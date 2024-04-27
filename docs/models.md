### Model/Resource Documentation

The following describes the tables/models compromising our relational database. Each model features a short description noting its purpose and key fields. A table listing field names, datatypes, and a short description of each field. 

*Developer's Note:* At this point, our tables largely reflect the JSON fields outputed by responses from the regulations.gov API. As we continue development, we intend to create at least one additional table to better align our data with our site. This table will store the outputs from our NLP models such as a plain English version of document titles, representative comments, topics, and sentiment measures that will be displayed to the user. We may also add `Users` and `Roles` tables if add in the ability to create accounts on the site. These features have currently been left out of our MVP. 

**Dockets**

`Dockets` represent collections of documents relevant to a proposed rule or notice. A given docket can contain documents available for commenting that represent the proposed rule change, along with supplementary documents, such as a cost-benefit analysis, that support the proposed rule. 

Since the dockets themselves are unavailable to comment on (only the documents contained within can recieve comments), we chose to collect only enough information to link docments to a docket (id) and other basic information (date, posting agency).


| Name              | Type                 | Description               |
| ----------------- | -------------------- | ------------------------- |
| id                | PrimaryKey (Dockets) | Regulations.gov UUID for a docket |
| docketType       | CharField             | Type of docket (i.e. Rulemaking, Nonrulemaking)       |
| lastModifiedDate | DateTime | Date docket was last updated   |
| agencyID  |  CharField  | ID of agency who posted docket |
| objectID | CharField  |  Regulations.gov UUID for API response object | 

**PublicComments**

`PublicComments` represents an individual comment posted to a document. Each comment features its own UUID (`id`) and is linked to its corresponding document by the `document` id (also links this table to the `Documents` table). Each comment is represented by the text of the comment, along with any available information collected by Regulations.gov on the comment. This data describes both the comment, such as wether the comment was withdrawn by the user, if the commented was posted to a restricted document (only open to certain agencies or interest groups), or the number of comments that feature the same text. 

This table also stores data on individuals who posted a comment, including their name, location, and organization. 


| Name              | Type                 | Description               |
| ----------------- | -------------------- | ------------------------- |
| id | PrimaryKey (Comment) | Regulations.gov UUID for a document |
| commentOn   | CharField  | Document the commnent is posted to  |
| document | ForeignKey (Documents) | Document ID a comment is posted to   |
| duplicateComments  |  IntegerField  | Number of duplicate comments |
| stateProvinceRegion | CharField  | State or province a comment is posted from | 
| subtype | CharField | Classifier for source of comment (e.g Member of Congress, Mass Mail Campaign) |
| objectId | CharField | Regulations.gov UUID for API response object |
| comment| TextField | Text of comment |
| firstName | CharField | First name of commenter |
| lastName| CharField | Last name of commenter |
| address1 | CharField | First line of commenter's address |
| address2 | CharField | Second line of commenter's address |
| city | CharField | City of the commenter's address |
| country | CharField | Commenter's country |
| email | EmailField | Email address of commenter |
| phone | CharField | Phone number of commenter |
| govAgency | CharField | Agency receiving comments |
| govAgencyType | CharField | Type of agency receiving comments |
| organization | CharField | Commenter's organization |
| originalDocumentId | CharField | Regulations.gov document ID |
| modifyDate | DateTime | Date the comment was last modified | 
| pageCount | IntegerField | Number of pages for the comment |
| postedDate | DateTime | Date the comment was inital posted |
| receiveDate | DateTime | Date comment was recieved by posting agency |
| title | CharField | Title of the commenter |
| withdrawn | Boolean | Bool if the comment was withdrawn |
| reasonWithdrawn | CharField | User submitted reason a comment was withdrawn |
| zip | charField | Zip code of the commenter |
| restrictReasonType | CharField | If document has been restricted for comment to certain users |
| restrictReason | CharField | Summary of reason for comment restriction |
| submitterRep | CharField | ??? |
| submitterRepAddress | CharField | ??? | 
| submitterRepCityState | CharField | ??? | 


**Documents**

`Documents` stores metadata on documents that can have comments posted to. To minimize our data intake, CivicLens only collects documents labeled as open-for-comments by the Federal Government. This does not mean that every document we collect features posted comments, but that some subset of the public is able to comment on each document. Each document also stores a URL to the Federal Registrar's XML version of the full document text (`fullTextXmlUrl`). This is used to extract the full text of the proposed rule which is not available through Regulations.gov. `summary` contains the plain English summary of the rule written by the Federal government which will be available on our site under the `/documents/` endpoint.

| Name              | Type                 | Description               |
| ----------------- | -------------------- | ------------------------- |
| id                | PrimaryKey (Documents) | Regulations.gov UUID for a document |
| documentType       | CharField             | Type of document (i.e. Proposed Rule, Notice)       |
| lastModifiedDate | DateTime | Date document was last updated   |
| withdrawn | BooleanField  |  Boolean if the documentment was withdrawn | 
| agencyID | CharField | ID of agency who posted document |
| commentEndDate| DateTime | End date of document commenting period |
| commentStartDate | DateTime | Start date of document commenting period |
| objectId | CharField | Regulations.gov UUID for API response object |
| fullTextXmlUrl | URL | Link to Federal Registar's XML text of rule |
| subAgy | CharField | Relevant office or department of posting agency |
| agencyType | CharField | Name of posting agency (e.g. FDA) |
| CRF | CharField | Code of Federal Regulations number |
| RIN | CharField | Regulation Identification Number used by Federal Register |
| title | CharField | Regulations.gov document title |
| summary | TextField | Plain English summary of document |
| furtherInformation | TextField | Additional information provided with document |