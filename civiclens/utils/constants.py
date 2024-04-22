import os
from dotenv import load_dotenv

load_dotenv(override=True)  # intentionally override any existing set env vars

DJANGO_SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
OLD_DJANGO_SECRET_KEY = os.environ.get("OLD_DJANGO_SECRET_KEY")
DATABASE_NAME = os.environ.get("DATABASE_NAME")
DATABASE_USER = os.environ.get("DATABASE_USER")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")
DATABASE_HOST = os.environ.get("DATABASE_HOST")
DATABASE_PORT = os.environ.get("DATABASE_PORT")
DATABASE_SSLMODE = os.environ.get("DATABASE_SSLMODE")

REG_GOV_API_KEY = os.environ.get("REG_GOV_API_KEY")