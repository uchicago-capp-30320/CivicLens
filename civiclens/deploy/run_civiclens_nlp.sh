#!/bin/bash

# set paths
PROJECT_DIR="/home/civiclens-nlp/CivicLens/"
# fetch droplet ID for instance deletion
DROPLET_ID=$(curl "http://169.254.169.254/metadata/v1/id")
echo "export DROPLET_ID=$DROPLET_ID" >> ~/.zshenv
source ~/.zshenv

echo "===================================="
echo "Running NLP Update..."

# go to project directory if exists
if [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR"
else
    echo "Project directory does not exist."
    exit 1
fi

# install dependencies
poetry install

# Run NLP update
poetry run python3 -m civiclens.nlp.pipeline --cloud
