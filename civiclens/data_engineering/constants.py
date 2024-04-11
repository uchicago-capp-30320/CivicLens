import os

API_KEY = os.getenv("REG_GOV_API_KEY")
if not API_KEY:  # if not saved locally, use the publicly available, but restricted, key
    API_KEY = "DEMO_KEY"
