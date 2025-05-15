#!/usr/bin/env python3
# main.py

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
    # Use os.path.join() to ensure platform-agnostic paths
    data_folder = os.path.join(CONFIG["data_folder"])
    logs_folder = os.path.join(CONFIG["logs_folder"])
    output_json = os.path.join(CONFIG["output_json"])
    output_mxf = os.path.join(CONFIG["output_mxf"])
    log_file = os.path.join(CONFIG["log_file"])

    os.makedirs(data_folder, exist_ok=True)
    os.makedirs(logs_folder, exist_ok=True)
    setup_logging(log_file)

    # Debugging: Log the current working directory and paths
    logging.info(f"Current working directory: {os.getcwd()}")
    logging.info(f"Data folder: {data_folder}")
    logging.info(f"Logs folder: {logs_folder}")
    logging.info(f"Log file: {log_file}")
    logging.info(f"Output JSON: {output_json}")
    logging.info(f"Output MXF: {output_mxf}")

    try:
        credentials = load_credentials()
        urls = get_api_urls(
            credentials["user_id"], "de9ee6e5-0d21-426b-87d7-be11545055d2"
        )  # noqa: E501

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
            save_json_data(combined_data, output_json)

        generate_mxf(combined_data, output_mxf)

    except Exception as e:
        logging.error(f"Error during execution: {e}")
        raise


if __name__ == "__main__":
    main()
