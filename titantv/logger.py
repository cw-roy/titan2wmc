#!/usr/bin/env python3

import logging
import os

from titantv.config import CONFIG


def setup_logging():
    os.makedirs(CONFIG["logs_folder"], exist_ok=True)
    handlers = []
    if CONFIG["log_to_console"]:
        handlers.append(logging.StreamHandler())
    if CONFIG["log_to_file"]:
        handlers.append(logging.FileHandler(CONFIG["log_file"], mode="a"))

    logging.basicConfig(
        level=getattr(logging, CONFIG["log_level"].upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )
    logging.info("Script started.")
    logging.info(f"Debug mode is {'ON' if CONFIG['debug_mode'] else 'OFF'}")

