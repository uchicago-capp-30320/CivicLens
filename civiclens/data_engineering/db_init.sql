
-- 1. USER MANAGEMENT
-- Create the role table
CREATE TABLE role (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Insert some initial data into the role table
INSERT INTO role (name, description) VALUES ('Admin', 'Administrator with full access');
INSERT INTO role (name, description) VALUES ('User', 'Standard user with limited access');

-- Create the user table
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role_id INTEGER,
    FOREIGN KEY (role_id) REFERENCES role(id)
);

-- 2. DATA FROM REGULATIONS GOV
-- Create the Dockets table
CREATE TABLE Dockets (
    id VARCHAR(255) PRIMARY KEY,
    docketType VARCHAR(255),
    lastModifiedDate TIMESTAMP WITH TIME ZONE,
    agencyId VARCHAR(50),
    title TEXT,
    objectId VARCHAR(255)
);

-- Create the Documents table
CREATE TABLE Documents (
    id VARCHAR(255) PRIMARY KEY,
    documentType VARCHAR(255),
    lastModifiedDate TIMESTAMP WITH TIME ZONE,
    frDocNum VARCHAR(255),
    withdrawn BOOLEAN,
    agencyId VARCHAR(50),
    commentEndDate DATE,
    title TEXT,
    postedDate DATE,
    docketId VARCHAR(255) REFERENCES Dockets(id),
    subtype VARCHAR(255),
    commentStartDate DATE,
    openForComment BOOLEAN
);

-- Create the Comments table
CREATE TABLE Comments (
    id VARCHAR(255) PRIMARY KEY,
    commentOn VARCHAR(255),
    commentOnDocumentId VARCHAR(255) REFERENCES Documents(id),
    duplicateComments INT,
    comment TEXT,
    firstName VARCHAR(255),
    lastName VARCHAR(255),
    modifyDate TIMESTAMP WITH TIME ZONE,
    pageCount INT,
    postedDate DATE,
    receiveDate DATE,
    title TEXT,
    trackingNbr VARCHAR(255),
    withdrawn BOOLEAN
);
