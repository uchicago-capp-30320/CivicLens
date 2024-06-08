#!/bin/bash

LOG_DIR="/usr/civiclens/log"
LAST_UPDATE_FILE="${LOG_DIR}/getdata.csv"
TODAY=$(date +'%Y-%m-%d')

# Check if the last update date file exists and read the last date
if [ -f "$LAST_UPDATE_FILE" ] && [ -s "$LAST_UPDATE_FILE" ]; then
    LASTDATE=$(tail -n 1 "$LAST_UPDATE_FILE" | cut -d ',' -f 1)
else
    LASTDATE=$(date -d "yesterday" +'%Y-%m-%d')
    echo "${LASTDATE}, INFO, Defaulted to yesterday's date as no previous log was found" >> "$LAST_UPDATE_FILE"
fi

# go to project directory
cd /home/CivicLens

# Run
if poetry run python3 -m civiclens.collect.move_data_from_api_to_database "${LASTDATE}" "${TODAY}" -k -d -c; then
    # Log success
    echo "$(date +'%Y-%m-%d %H:%M:%S'), SUCCESS, Data collection completed successfully" >> "$LAST_UPDATE_FILE"
else
    # Log failure
    echo "$(date +'%Y-%m-%d %H:%M:%S'), ERROR, Data collection failed" >> "$LAST_UPDATE_FILE"
    exit 1
fi
