import requests
import psycopg2

# API endpoint for Dockets
api_url = "https://api.regulations.gov/v4/dockets"

# Fetch data from API
response = requests.get(api_url)
dockets_data = response.json()

# Database connection parameters
db_params = {
    "dbname": "CivicLens",
    "user": "your_username",
    "password": "your_password",
    "host": "localhost"
}

# Connect to the PostgreSQL database
conn = psycopg2.connect(**db_params)
cur = conn.cursor()

# Insert data into the Dockets table
for docket in dockets_data['data']:  # Assuming 'data' contains the list of dockets
    sql = """
    INSERT INTO Dockets (id, docketType, lastModifiedDate, agencyId, title, objectId)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET
    docketType = EXCLUDED.docketType,
    lastModifiedDate = EXCLUDED.lastModifiedDate,
    agencyId = EXCLUDED.agencyId,
    title = EXCLUDED.title,
    objectId = EXCLUDED.objectId;
    """
    cur.execute(sql, (
        docket['id'],
        docket['attributes']['docketType'],
        docket['attributes']['lastModifiedDate'],
        docket['attributes']['agencyId'],
        docket['attributes']['title'],
        docket['attributes']['objectId']
    ))

# Commit changes and close the connection
conn.commit()
cur.close()
conn.close()
