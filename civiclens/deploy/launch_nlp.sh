#!/bin/bash

cd /home/civiclens/CivicLens
poetry run python3 -m civiclens.deploy.launch

# crontab command to run the nlp update at midnight on wednesday every week
# 0 0 * * 3 /home/CivicLens/civiclens/deploy/launch_nlp.sh (fix with linux server path)
