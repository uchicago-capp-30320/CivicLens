# set paths for logging nlp batch info
LOG_DIR="/usr/civiclens/log"
LAST_UPDATE_FILE="${LOG_DIR}/nlp_batch.csv"

# go to project directory
if [ -d "/home/CivicLens" ]; then
    cd /home/CivicLens
else
    echo "Project directory does not exist."
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

# crontab command to run the nlp update at midnight on wednesday every week
# 0 0 * * 3 /home/CivicLens/civiclens/utils/run_civiclens_nlp.sh (fix with linux server path)
