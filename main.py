import logging
import os
from datetime import datetime

import orjson
import pytz
import requests
from dotenv import load_dotenv


def setup_logging(log_file):
    """Configure logging settings."""
    logging.basicConfig(
        filename=log_file,
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info("Script started.")


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


def fetch_json(url, headers):
    """Fetch and return JSON data from an API endpoint."""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching data from {url}: {e}")
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


def save_json_data(data, output_file):
    """Save processed data to JSON file."""
    try:
        with open(output_file, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        logging.info(f"Data written to {output_file}")
    except Exception as e:
        logging.error(f"Failed to write output file: {e}")
        raise


def main():
    """Main execution function."""
    # Create output directories
    data_folder = "data"
    logs_folder = "logs"
    os.makedirs(data_folder, exist_ok=True)
    os.makedirs(logs_folder, exist_ok=True)

    # Setup paths and logging
    output_file = os.path.join(data_folder, "api_output.json")
    log_file = os.path.join(logs_folder, "titantv.log")
    setup_logging(log_file)

    try:
        # Load credentials and configure API
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

        # Fetch data
        lineup_data = fetch_json(urls["lineup"], headers)
        channels_data = fetch_json(urls["channels"], headers)

        schedule_start = get_schedule_start_time()
        schedule_url = urls["schedule"].format(schedule_start=schedule_start)
        schedule_data = fetch_json(schedule_url, headers)

        # Process data
        combined_data = {
            "lineup": process_lineup_data(lineup_data),
            "channels": process_channels_data(channels_data),
            "schedule": process_schedule_data(schedule_data),
        }

        # Save results
        save_json_data(combined_data, output_file)
        print(f"Fetched and combined TitanTV listing data saved to: {output_file}")

    except Exception as e:
        logging.error(f"Error during execution: {e}")
        raise


if __name__ == "__main__":
    main()
