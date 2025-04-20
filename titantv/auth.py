#!/usr/bin/env python3
# auth.py

import os

from dotenv import load_dotenv


def load_credentials():
    load_dotenv()
    credentials = {
        "user_id": os.getenv("TITANTV_USER_ID"),
        "login_name": os.getenv("TITANTV_USERNAME"),
        "password": os.getenv("TITANTV_PASSWORD"),
        "lineup_id": os.getenv("TITANTV_LINEUP_ID"),
    }
    missing = [key for key, value in credentials.items() if not value]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    return credentials
