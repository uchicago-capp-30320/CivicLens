#!/bin/bash

# set paths for logging nlp batch info
LOG_DIR="/home/civiclens-nlp/CivicLens/civiclens/log"
LAST_UPDATE_FILE="${LOG_DIR}/nlp_batch.csv"
PROJECT_DIR="/home/civiclens-nlp/CivicLens/"
VENV_PATH="/home/civiclens-nlp/CivicLens/.venv/bin/activate"
DROPLET_ID=$(curl "http://169.254.169.254/metadata/v1/id")
echo "DROPLET_ID=$DROPLET_ID" >> /home/civiclens-nlp/.bashrc
source /home/civiclens-nlp/.bashrc

echo "===================================="
echo "Running NLP Update..."

# make sure logging directory exists
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
fi

# go to project directory if exists
if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
else
    echo "Project directory does not exist."
    exit 1
fi

# activate python virtual environment
source "$VENV_PATH"
poetry install

if ! source "$VENV_PATH"; then
    echo "Failed to activate virtual environment."
    exit 1
fi

# Run NLP update
if poetry run python3 -m civiclens.nlp.pipeline; then
    # Log success
    echo "$(date +'%Y-%m-%d %H:%M:%S'), SUCCESS, NLP updated completed successfully" >> "$LAST_UPDATE_FILE"
else
    # Log failure
    echo "$(date +'%Y-%m-%d %H:%M:%S'), ERROR, NLP update failed" >> "$LAST_UPDATE_FILE"
    exit 1
fi
