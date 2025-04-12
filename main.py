import logging
import os
from datetime import datetime

import orjson
import pytz
import requests
from dotenv import load_dotenv
from lxml import etree

# Debug mode flag
DEBUG_MODE = True  # Set to False in production to skip saving api_output.json
LOG_TO_FILE = True  # Set to False if only logging to console

def setup_logging(log_file):
    """Configure logging settings."""
    handlers = [logging.StreamHandler()]  # Always log to console

    if LOG_TO_FILE:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, mode='a'))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers
    )

    logging.info("Script started.")


# def setup_logging(log_file):
#     """Configure logging settings."""
#     logging.basicConfig(
#         filename=log_file,
#         filemode="a",
#         level=logging.INFO,
#         format="%(asctime)s - %(levelname)s - %(message)s",
#     )
#     logging.getLogger().addHandler(logging.StreamHandler())
#     logging.info("Script started.")


def load_credentials():
    """Load and validate environment variables."""
    load_dotenv()
    credentials = {
        "user_id": os.getenv("TITANTV_USER_ID"),
        "login_name": os.getenv("TITANTV_USERNAME"),
        "password": os.getenv("TITANTV_PASSWORD"),
    }
    if not all(credentials.values()):
        raise ValueError(
            "Missing required environment variables: "
            "TITANTV_USER_ID, TITANTV_USERNAME, TITANTV_PASSWORD"
        )
    return credentials


def get_api_urls(user_id, lineup_id):
    """Generate API endpoints."""
    return {
        "channels": f"https://titantv.com/api/channel/{user_id}/{lineup_id}",
        "lineup": f"https://titantv.com/api/lineup/{user_id}",
        "schedule": f"https://titantv.com/api/schedule/{user_id}/{lineup_id}/{{schedule_start}}/300",
        "user": f"https://titantv.com/api/user/{user_id}",
    }


def fetch_json(url, headers, label):
    """Fetch and return JSON data from an API endpoint."""
    try:
        logging.info(f"Fetching data from {label} API")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logging.info(f"{label} data fetched successfully.")
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching data from {label} API: {e}")
        raise


def get_schedule_start_time(timezone="America/Los_Angeles"):
    """Generate formatted schedule start time."""
    local_tz = pytz.timezone(timezone)
    local_time = datetime.now(local_tz)
    return local_time.strftime("%Y%m%d%H%M")


def process_lineup_data(lineup_data):
    """Extract relevant lineup information."""
    lineup = lineup_data["lineups"][0]
    return {
        "lineupId": lineup["lineupId"],
        "lineupName": lineup["lineupName"],
        "timezone": lineup["timeZone"],
        "utcOffset": lineup["utcOffset"],
        "observesDst": lineup["observesDst"],
    }


def process_channels_data(channels_data):
    """Process and format channel information."""
    channels = []
    for channel in channels_data.get("channels", []):
        channels.append(
            {
                "channelId": channel["channelId"],
                "callSign": channel["callSign"],
                "network": channel["network"],
                "description": channel["description"],
                "hdCapable": channel["hdCapable"],
                "logo": channel["logo"],
                "sortOrder": channel["sortOrder"],
                "majorChannel": channel["majorChannel"],
                "minorChannel": channel["minorChannel"],
            }
        )
    return channels


def process_schedule_data(schedule_data):
    """Process and format schedule information."""
    schedule = []
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                schedule.append(
                    {
                        "channelId": channel["channelIndex"],
                        "eventId": event["eventId"],
                        "startTime": event["startTime"],
                        "endTime": event["endTime"],
                        "title": event["title"],
                        "description": event["description"],
                        "programType": event["programType"],
                        "tvRating": event.get("tvRating", ""),
                        "showCard": event.get("showCard", ""),
                    }
                )
    return schedule


def generate_mxf(data, output_path):
    """Convert JSON data into MXF XML format and write to file."""
    logging.info("Generating MXF file...")
    mxf = etree.Element("MXF", xmlns="http://www.microsoft.com")

    lineup_elem = etree.SubElement(mxf, "Lineups")
    lineup = data["lineup"]
    lineup_node = etree.SubElement(
        lineup_elem, "Lineup", id="1", uid=lineup["lineupId"]
    )
    etree.SubElement(lineup_node, "Name").text = lineup["lineupName"]
    etree.SubElement(lineup_node, "TimeZone").text = lineup["timezone"]
    etree.SubElement(lineup_node, "UTCOffset").text = str(lineup["utcOffset"])
    etree.SubElement(lineup_node, "ObservesDaylightSaving").text = str(
        lineup["observesDst"]
    ).lower()

    channels_elem = etree.SubElement(mxf, "Channels")
    for ch in data["channels"]:
        ch_elem = etree.SubElement(channels_elem, "Channel", id=str(ch["channelId"]))
        etree.SubElement(ch_elem, "CallSign").text = ch["callSign"]
        etree.SubElement(ch_elem, "Name").text = ch["network"]
        etree.SubElement(ch_elem, "Description").text = ch["description"]
        etree.SubElement(ch_elem, "HD").text = str(ch["hdCapable"]).lower()
        etree.SubElement(ch_elem, "Logo").text = ch["logo"]
        etree.SubElement(ch_elem, "MajorChannel").text = str(ch["majorChannel"])
        etree.SubElement(ch_elem, "MinorChannel").text = str(ch["minorChannel"])
        etree.SubElement(ch_elem, "Lineup").text = "1"

    programs_elem = etree.SubElement(mxf, "Programs")
    for prog in data["schedule"]:
        prog_elem = etree.SubElement(programs_elem, "Program", id=str(prog["eventId"]))
        etree.SubElement(prog_elem, "Title").text = prog["title"]
        etree.SubElement(prog_elem, "Description").text = prog["description"]
        etree.SubElement(prog_elem, "StartTime").text = prog["startTime"]
        etree.SubElement(prog_elem, "EndTime").text = prog["endTime"]
        etree.SubElement(prog_elem, "ProgramType").text = prog["programType"]
        etree.SubElement(prog_elem, "TVRating").text = prog.get("tvRating", "")
        etree.SubElement(prog_elem, "ShowCard").text = prog.get("showCard", "")
        etree.SubElement(prog_elem, "Channel").text = str(prog["channelId"])

    tree = etree.ElementTree(mxf)
    tree.write(output_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
    logging.info(f"MXF file written to {output_path}")


def save_json_data(data, output_file):
    """Save processed data to JSON file."""
    try:
        with open(output_file, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        # logging.info(f"Data written to {output_file}")
    except Exception as e:
        logging.error(f"Failed to write output file: {e}")
        raise


def main():
    data_folder = "data"
    logs_folder = "logs"
    os.makedirs(data_folder, exist_ok=True)
    # os.makedirs(logs_folder, exist_ok=True)

    output_file = os.path.join(data_folder, "api_output.json")
    mxf_file = os.path.join(data_folder, "listings.mxf")
    log_file = os.path.join(logs_folder, "titantv.log")

    setup_logging(log_file)
    logging.info(f"Debug mode is {'ON' if DEBUG_MODE else 'OFF'}")

    try:
        credentials = load_credentials()
        urls = get_api_urls(
            credentials["user_id"], "de9ee6e5-0d21-426b-87d7-be11545055d2"
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) "
                "Gecko/20100101 Firefox/88.0"
            )
        }

        lineup_data = fetch_json(urls["lineup"], headers, "lineup")
        channels_data = fetch_json(urls["channels"], headers, "channels")
        schedule_start = get_schedule_start_time()
        schedule_url = urls["schedule"].format(schedule_start=schedule_start)
        schedule_data = fetch_json(schedule_url, headers, "schedule")

        combined_data = {
            "lineup": process_lineup_data(lineup_data),
            "channels": process_channels_data(channels_data),
            "schedule": process_schedule_data(schedule_data),
        }

        if DEBUG_MODE:
            save_json_data(combined_data, output_file)
            logging.info(f"DEBUG_MODE enabled — JSON data written to {output_file}")
        else:
            logging.info("DEBUG_MODE disabled — skipping JSON data save.")

        try:
            generate_mxf(combined_data, mxf_file)
        except Exception as e:
            logging.error(f"Failed to generate MXF file: {e}")

    except Exception as e:
        logging.error(f"Error during execution: {e}")
        raise


if __name__ == "__main__":
    main()
