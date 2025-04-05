import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from auth import login, validate_user, validate_lineup
from fetch import fetch_provider_info, fetch_lineup_info, fetch_channel_info, fetch_schedule
from extract import extract_programs, extract_schedule_entries, extract_cast_and_crew, extract_guide_images
from processing import generate_mxf

# Load environment variables from .env file
load_dotenv()

# TitanTV API Endpoints
USER_URL = "https://titantv.com/api/user/{user_id}"
LINEUP_URL = "https://titantv.com/api/lineup/{user_id}"
CHANNEL_URL = "https://titantv.com/api/channel/{user_id}/{lineup_id}"
SCHEDULE_URL = "https://titantv.com/api/schedule/{user_id}/{lineup_id}/{start_time}/{duration}"

# Retrieve credentials and user ID from environment variables
USERNAME = os.getenv("TITANTV_USERNAME")
PASSWORD = os.getenv("TITANTV_PASSWORD")
USER_ID = os.getenv("TITANTV_USER_ID")

# Headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Referer": "https://titantv.com/",
    "Content-Type": "application/json"
}

# Set up logging
logging.basicConfig(filename="titantv.log", level=logging.INFO, format="%(asctime)s - %(message)s")

DEFAULT_DURATION = "300"


def login_and_validate(session):
    """Handles login and validation of user and lineup."""
    logging.info("[+] Logging in and validating user and lineup...")

    # Login
    session = login(session, USERNAME, PASSWORD, HEADERS)
    if not session:
        logging.error("[-] Login failed. Exiting.")
        exit(1)

    # Validate user
    user_url = USER_URL.format(user_id=USER_ID)
    if not validate_user(session, user_url, HEADERS):
        logging.error("[-] User validation failed. Exiting.")
        exit(1)

    # Validate lineup
    lineup_url = LINEUP_URL.format(user_id=USER_ID)
    if not validate_lineup(session, lineup_url, HEADERS):
        logging.error("[-] Lineup validation failed. Exiting.")
        exit(1)

    logging.info("[+] Login and validation successful.")
    return user_url, lineup_url


def fetch_data(session, user_url, lineup_url):
    """Fetches provider, lineup, channel, and schedule data."""
    logging.info("[+] Fetching data...")

    # Fetch provider information
    provider_info = fetch_provider_info(session, user_url, HEADERS)
    if not provider_info:
        logging.error("[-] Failed to fetch provider information. Exiting.")
        exit(1)

    # Fetch lineup information
    lineup_info = fetch_lineup_info(session, lineup_url, HEADERS)
    if not lineup_info:
        logging.error("[-] Failed to fetch lineup information. Exiting.")
        exit(1)

    # Fetch channel information
    channel_url = CHANNEL_URL.format(user_id=USER_ID, lineup_id=lineup_info["lineupId"])
    channels = fetch_channel_info(session, channel_url, HEADERS)
    if not channels:
        logging.error("[-] Failed to fetch channel information. Exiting.")
        exit(1)

    # Fetch schedule
    start_time = datetime.now().strftime("%Y%m%d%H%M")
    schedule_url = SCHEDULE_URL.format(user_id=USER_ID, lineup_id=lineup_info["lineupId"], start_time=start_time, duration=DEFAULT_DURATION)
    schedule_data = fetch_schedule(session, schedule_url, HEADERS)
    if not schedule_data:
        logging.error("[-] Failed to fetch schedule. Exiting.")
        exit(1)

    logging.info("[+] Data fetched successfully.")
    return provider_info, lineup_info, channels, schedule_data


def process_data(schedule_data, channels):
    """Processes the fetched data to extract programs, schedule entries, cast and crew, and guide images."""
    logging.info("[+] Processing data...")

    programs = extract_programs(schedule_data)
    schedule_entries = extract_schedule_entries(schedule_data)
    cast_and_crew = extract_cast_and_crew(schedule_data)
    guide_images = extract_guide_images(schedule_data, channels)

    logging.info("[+] Data processed successfully.")
    return programs, schedule_entries, cast_and_crew, guide_images


def generate_output(provider_info, lineup_info, channels, schedule_data):
    """Generates the MXF file and saves it."""
    logging.info("[+] Generating MXF file...")

    # Generate the MXF file
    mxf_content = generate_mxf(provider_info, lineup_info, channels, schedule_data)

    # Save the MXF file
    with open("output.mxf", "w", encoding="utf-8") as file:
        file.write(mxf_content)

    logging.info("[+] Successfully generated output.mxf.")


if __name__ == "__main__":
    try:
        logging.info("[+] Start run...")

        # Start a session
        session = requests.Session()

        # Step 1: Login and validate
        user_url, lineup_url = login_and_validate(session)

        # Step 2: Fetch data
        provider_info, lineup_info, channels, schedule_data = fetch_data(session, user_url, lineup_url)

        # Step 3: Process data
        process_data(schedule_data, channels)

        # Step 4: Generate output
        generate_output(provider_info, lineup_info, channels, schedule_data)

    finally:
        if session:
            session.close()
            logging.info("[+] Session closed.")
