### titantv/api.py
import logging
import random

import requests

from titantv.config import USER_AGENTS

session = requests.Session()

def get_api_urls(user_id, lineup_id):
    return {
        "channels": f"https://titantv.com/api/channel/{user_id}/{lineup_id}",
        "lineup": f"https://titantv.com/api/lineup/{user_id}",
        "schedule": f"https://titantv.com/api/schedule/{user_id}/{lineup_id}/{{schedule_start}}/300",
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
