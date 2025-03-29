import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# TitanTV API Endpoints
USER_URL = "https://titantv.com/api/user/{user_id}"  # Replace with dynamic user ID
LINEUP_URL = "https://titantv.com/api/lineup/{user_id}"  # Replace with dynamic user ID
SCHEDULE_URL = "https://titantv.com/api/schedule/{user_id}/{lineup_id}/{start_time}/{duration}"

# Retrieve credentials and user ID from environment variables
USERNAME = os.getenv("TITANTV_USERNAME")
PASSWORD = os.getenv("TITANTV_PASSWORD")
USER_ID = os.getenv("TITANTV_USER_ID")  # User ID should be stored in the .env

# Headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Referer": "https://titantv.com/",
    "Content-Type": "application/json"
}

# Start a session
session = requests.Session()

# Set up logging
logging.basicConfig(filename="titantv.log", level=logging.INFO, format='%(asctime)s - %(message)s')

if not USERNAME or not PASSWORD or not USER_ID:
    logging.error("[-] Missing required environment variables. Please check your .env file.")
    exit(1)

DEFAULT_DURATION = "300"

# Utility Functions
def get_current_start_time():
    """Generate start time based on the current date and time."""
    now = datetime.now()  # Get current date and time
    start_time = now.strftime("%Y%m%d%H%M")  # Format the date as 'YYYYMMDDHHMM'
    return start_time

# Core Functions
def login():
    """Logs into TitanTV and prints out cookies and response content to help debug UUID."""
    if not USERNAME or not PASSWORD:
        print("[-] Missing credentials. Please set TITANTV_USERNAME and TITANTV_PASSWORD in the .env file.")
        logging.error("Missing credentials.")
        return None

    payload = {"loginName": USERNAME, "password": PASSWORD}

    login_url = "https://titantv.com/api/login"
    response = session.post(login_url, json=payload, headers=HEADERS)

    if response.status_code == 200 and "Set-Cookie" in response.headers:
        logging.info("[+] Login successful!")
        return session
    else:
        logging.error("[-] Login failed.")
        logging.error(f"Response: {response.text}")
        return None

def validate_user():
    """Fetches user data to validate user ID and lineup."""
    logging.info("[+] Validating user ID...")

    # Construct URL dynamically based on user ID
    url = USER_URL.format(user_id=USER_ID)
    response = session.get(url, headers=HEADERS)

    if response.status_code == 200:
        logging.info("[+] User validated successfully.")
        return True
    else:
        logging.error(f"[-] Failed to validate user ID. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return False

def validate_lineup():
    """Fetches lineup data to validate lineup ID."""
    logging.info("[+] Validating provider lineup...")

    # Construct URL dynamically based on user ID
    url = LINEUP_URL.format(user_id=USER_ID)
    response = session.get(url, headers=HEADERS)

    if response.status_code == 200:
        logging.info("[+] Provider lineup validated successfully.")
        return True
    else:
        logging.error(f"[-] Failed to validate lineup. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return False

def fetch_schedule(lineup_id, start_time, duration):
    """Fetches TV schedule for the given lineup and time range."""
    logging.info("[+] Fetching schedule...")
    url = SCHEDULE_URL.format(user_id=USER_ID, lineup_id=lineup_id, start_time=start_time, duration=duration)
    
    for attempt in range(3):  # Retry up to 3 times
        response = session.get(url, headers=HEADERS)
        if response.status_code == 200:
            try:
                schedule_data = response.json()
                logging.info("[+] Schedule data parsed successfully.")
                return schedule_data
            except ValueError as e:
                logging.error(f"[-] Error parsing JSON: {e}")
                return None
        elif response.status_code == 401:
            logging.error("[-] Unauthorized. Check your credentials.")
            return None
        elif response.status_code >= 500:
            logging.warning(f"[!] Server error (status {response.status_code}). Retrying...")
        else:
            logging.error(f"[-] Failed to fetch schedule. Status code: {response.status_code}")
            logging.error(f"[-] Response content: {response.text}")
            return None
    logging.error("[-] All retries failed.")
    return None

# Data Processing Functions
def extract_listings(schedule_data):
    """Extracts and processes TV listings from the fetched schedule data."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    listings = []
    
    # Ensure the response has 'channels'
    if "channels" in schedule_data:
        for channel in schedule_data["channels"]:
            if "days" in channel:
                for day in channel["days"]:
                    if "events" in day:
                        for event in day["events"]:
                            try:
                                event_details = {
                                    "title": event.get("title", "N/A"),
                                    "episode_title": event.get("episodeTitle", "N/A"),
                                    "start_time": event.get("startTime", "N/A"),
                                    "end_time": event.get("endTime", "N/A"),
                                    "duration": event.get("duration", "N/A"),
                                    "channel_index": channel.get("channelIndex", "N/A"),
                                    "description": event.get("description", "N/A"),
                                    "display_genre": event.get("displayGenre", "N/A"),
                                    "show_card": event.get("showCard", ""),
                                }
                                listings.append(event_details)
                            except KeyError as e:
                                logging.error(f"[-] Missing expected key: {e}")
    else:
        logging.error("[-] No 'channels' found in schedule data.")
    
    return listings

# Main Execution Block
if __name__ == "__main__":
    try:
        logging.info("[+] Start run...")
        session = login()
        if session:
            logging.info("[+] Ready to proceed with user and provider validation.")
            
            # Validate user and lineup
            if validate_user() and validate_lineup():
                # If both validations are successful, proceed to fetch schedule (replace with actual lineup_id and duration)
                lineup_id = "de9ee6e5-0d21-426b-87d7-be11545055d2"  # Example lineup ID (replace with actual)
                start_time = get_current_start_time()  # Use dynamic current start time
                duration = "300"  # Example duration in minutes (replace with actual)
                
                schedule_data = fetch_schedule(lineup_id, start_time, duration)
                if schedule_data:
                    # Extract and log the TV listings
                    listings = extract_listings(schedule_data)
                    if listings:
                        logging.info(f"[+] Found {len(listings)} listings.")
                    else:
                        logging.error("[-] No listings found.")
            else:
                logging.error("[-] User and provider validation failed.")
        logging.info("[+] End of run.")
    finally:       
        if session:
            session.close()
            logging.info("[+] Session closed.")
