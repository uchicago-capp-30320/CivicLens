-- Creating the Role table
CREATE TABLE Role (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT
);

-- Creating the User table
CREATE TABLE User (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role_id INT,
    FOREIGN KEY (role_id) REFERENCES Role(id)
);

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
    title TEXT,
    docketId VARCHAR(255) REFERENCES Dockets(id),
    subtype VARCHAR(255),
    commentStartDate DATE,
    openForComment BOOLEAN,
    objectId VARCHAR(100)
);

-- Creating the Comments table
CREATE TABLE Comments (
    id VARCHAR(255) PRIMARY KEY,
    objectId VARCHAR(255) NOT NULL,
    commentOn VARCHAR(255),
    commentOnDocumentId TIMESTAMP REFERENCES Documents(id),
    duplicateComments INT,
    stateProvinceRegion VARCHAR(100),
    subtype VARCHAR(100),
    comment TEXT,
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
    title TEXT,
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

-- Creating the Summaries table
CREATE TABLE Summaries (
    id VARCHAR(255) PRIMARY KEY,
    frDocNum VARCHAR(100) REFERENCES Documents(frDocNum),
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
