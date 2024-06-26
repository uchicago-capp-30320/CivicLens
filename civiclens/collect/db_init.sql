-- Creating the Dockets table
CREATE TABLE Dockets (
    id VARCHAR(255) PRIMARY KEY,
    docketType VARCHAR(255),
    lastModifiedDate TIMESTAMP,
    agencyId VARCHAR(100),
    title TEXT,
    objectId VARCHAR(255),
    highlightedContent VARCHAR(255)
);
-- Creating the Documents table
CREATE TABLE Documents (
    id VARCHAR(255) PRIMARY KEY,
    documentType VARCHAR(255),
    lastModifiedDate TIMESTAMP,
    frDocNum VARCHAR(100),
    withdrawn BOOLEAN,
    agencyId VARCHAR(100),
    commentEndDate DATE,
    postedDate DATE,
    docTitle TEXT,
    docketId VARCHAR(255) REFERENCES Dockets(id),
    subtype VARCHAR(255),
    commentStartDate DATE,
    openForComment BOOLEAN,
    objectId VARCHAR(100),
    fullTextXmlUrl VARCHAR(255),
    subAgy VARCHAR(255),
    agencyType VARCHAR(100),
    CFR VARCHAR(100),
    RIN VARCHAR(100),
    title VARCHAR(255),
    summary TEXT,
    dates VARCHAR(255),
    furtherInformation TEXT,
    supplementaryInformation TEXT,
    fullText TEXT
);
-- Creating the Comments table
CREATE TABLE PublicComments (
    id VARCHAR(255) PRIMARY KEY,
    objectId VARCHAR(255) NOT NULL,
    commentOn VARCHAR(255),
    commentOnDocumentId VARCHAR(255) REFERENCES Documents(id),
    duplicateComments INT,
    stateProvinceRegion VARCHAR(100),
    subtype VARCHAR(100),
    publicComment TEXT,
    firstName VARCHAR(255),
    lastName VARCHAR(255),
    address1 VARCHAR(200),
    address2 VARCHAR(200),
    city VARCHAR(100),
    category VARCHAR(100),
    country VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50),
    govAgency VARCHAR(100),
    govAgencyType VARCHAR(100),
    organization VARCHAR(255),
    originalDocumentId VARCHAR(100),
    modifyDate TIMESTAMP,
    pageCount INT,
    postedDate DATE,
    receiveDate DATE,
    commentTitle TEXT,
    trackingNbr VARCHAR(255),
    withdrawn BOOLEAN,
    reasonWithdrawn VARCHAR(255),
    zip VARCHAR(50),
    restrictReason VARCHAR(100),
    restrictReasonType VARCHAR(100),
    submitterRep VARCHAR(100),
    submitterRepAddress VARCHAR(255),
    submitterRepCityState VARCHAR(100)
);
-- Create the nlp_output table
CREATE TABLE nlp_output (
    document_id VARCHAR(255) REFERENCES document(id) ON DELETE CASCADE,
    rep_comments TEXT,
    doc_plain_english_title VARCHAR(255),
    num_total_comments INTEGER DEFAULT 0,
    num_unique_comments INTEGER DEFAULT 0,
    num_representative_comment INTEGER DEFAULT 0,
    topics TEXT,
    num_topics INTEGER DEFAULT 0,
    nlp_last_updated TIMESTAMP
);
