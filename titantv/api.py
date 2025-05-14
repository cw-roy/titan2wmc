#!/usr/bin/env python3
# api.py

import logging
import random
from datetime import datetime

import requests

from titantv.config import USER_AGENTS

session = requests.Session()


def get_api_urls(user_id, lineup_id):
    # Get the current system time in the required format (YYYYMMDDHHMM)
    schedule_start = datetime.now().strftime("%Y%m%d%H%M")

    # Set the duration in minutes. 24 hours = 1440 minutes
    # 14 days = 14 * 24 * 60 = 20160 minutes
    duration = 20160

    return {
        "channels": f"https://titantv.com/api/channel/{user_id}/{lineup_id}",
        "lineup": f"https://titantv.com/api/lineup/{user_id}",
        # Use the dynamic schedule start and fixed duration in the URL
        "schedule": f"https://titantv.com/api/schedule/{user_id}/{lineup_id}/{schedule_start}/{duration}",
        "user": f"https://titantv.com/api/user/{user_id}",
    }


def fetch_json(url, label):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        logging.info(f"Fetching data from {label} API")
        response = session.get(url, headers=headers)
        response.raise_for_status()
        logging.info(f"{label} data fetched successfully.")
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching data from {label} API: {e}")
        raise
