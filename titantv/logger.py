#!/usr/bin/env python3
# logger.py

import logging
import os

from titantv.config import CONFIG


def setup_logging(log_file):
    # Use os.path.join() to ensure platform-agnostic paths
    logs_folder = os.path.join(CONFIG["logs_folder"])
    os.makedirs(logs_folder, exist_ok=True)

    handlers = []
    if CONFIG["log_to_console"]:
        handlers.append(logging.StreamHandler())
    if CONFIG["log_to_file"]:
        log_file_path = os.path.join(
            logs_folder, log_file
        )  # Use os.path.join() for log file
        handlers.append(logging.FileHandler(log_file_path, mode="a"))

    logging.basicConfig(
        level=getattr(logging, CONFIG["log_level"].upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )
    logging.info("Script started.")
    logging.info(f"Debug mode is {'ON' if CONFIG['debug_mode'] else 'OFF'}")
