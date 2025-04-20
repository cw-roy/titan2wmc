#!/usr/bin/env python3
# auth.py

import os

from dotenv import load_dotenv


def load_credentials():
    load_dotenv()

    # Define the environment variables and their corresponding names
    credentials = {
        "user_id": os.getenv("TITANTV_USER_ID"),
        "lineup_id": os.getenv("TITANTV_LINEUP_ID"),
        "login_name": os.getenv("TITANTV_USERNAME"),
        "password": os.getenv("TITANTV_PASSWORD"),
    }

    # Check for missing variables and build a list of missing ones
    missing_vars = [key for key, value in credentials.items() if value is None]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    return credentials
