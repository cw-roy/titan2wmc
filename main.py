#!/usr/bin/env python3

import logging
import os

# from titantv import config
from titantv.api import fetch_json, get_api_urls
from titantv.auth import load_credentials
from titantv.config import CONFIG
from titantv.logger import setup_logging
from titantv.mxf_generator import generate_mxf
from titantv.processor import (
    process_channels_data,
    process_lineup_data,
    process_schedule_data,
)
from titantv.utils import get_schedule_start_time, save_json_data


def main():
    os.makedirs(CONFIG["data_folder"], exist_ok=True)
    setup_logging()

    try:
        credentials = load_credentials()
        urls = get_api_urls(credentials["user_id"], "de9ee6e5-0d21-426b-87d7-be11545055d2")  # noqa: E501

        lineup_data = fetch_json(urls["lineup"], "lineup")
        channels_data = fetch_json(urls["channels"], "channels")
        schedule_start = get_schedule_start_time()
        schedule_url = urls["schedule"].format(schedule_start=schedule_start)
        schedule_data = fetch_json(schedule_url, "schedule")

        combined_data = {
            "lineup": process_lineup_data(lineup_data),
            "channels": process_channels_data(channels_data),
            "schedule": process_schedule_data(schedule_data),
        }

        if CONFIG["debug_mode"]:
            save_json_data(combined_data, CONFIG["output_json"])

        generate_mxf(combined_data, CONFIG["output_mxf"])

    except Exception as e:
        logging.error(f"Error during execution: {e}")
        raise


if __name__ == "__main__":
    main()
