#!/bin/bash

echo "Running backup_postgres.sh..."

DATE=$(date +'%Y-%m-%d-%H%M%S')

BACKUP_FILE="/usr/backup/civiclens_${DATE}.dump"
LOG_FILE="/usr/backup/log/${DATE}.log"

# Perform the backup
pg_dump $DB_CONNECTION --file=$BACKUP_FILE > $LOG_FILE 2>&1
