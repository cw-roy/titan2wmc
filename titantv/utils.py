#!/usr/bin/env python3
# utils.py

import logging
from datetime import datetime

import orjson
import pytz


def get_schedule_start_time(timezone="America/Los_Angeles"):
    local_tz = pytz.timezone(timezone)
    local_time = datetime.now(local_tz)
    return local_time.strftime("%Y%m%d%H%M")


def save_json_data(data, output_file):
    try:
        with open(output_file, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        logging.info(f"Data written to {output_file}")
    except Exception as e:
        logging.error(f"Failed to write output file: {e}")
        raise
