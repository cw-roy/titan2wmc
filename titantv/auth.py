### titantv/auth.py
import os

from dotenv import load_dotenv


def load_credentials():
    load_dotenv()
    credentials = {
        "user_id": os.getenv("TITANTV_USER_ID"),
        "login_name": os.getenv("TITANTV_USERNAME"),
        "password": os.getenv("TITANTV_PASSWORD"),
    }
    if not all(credentials.values()):
        raise ValueError("Missing required environment variables: TITANTV_USER_ID, TITANTV_USERNAME, TITANTV_PASSWORD")  # noqa: E501
    return credentials