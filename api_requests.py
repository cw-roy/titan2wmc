import requests
import logging
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# TitanTV API Endpoints
USER_URL = "https://titantv.com/api/user/{user_id}"
LINEUP_URL = "https://titantv.com/api/lineup/{user_id}"
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

# Start a session
session = requests.Session()

def login():
    """Logs into TitanTV and returns the session."""
    if not USERNAME or not PASSWORD:
        logging.error("[-] Missing credentials. Please set TITANTV_USERNAME and TITANTV_PASSWORD in the .env file.")
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
    """Fetches user data to validate user ID."""
    logging.info("[+] Validating user ID...")
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
    url = LINEUP_URL.format(user_id=USER_ID)
    response = session.get(url, headers=HEADERS)

    if response.status_code == 200:
        logging.info("[+] Provider lineup validated successfully.")
        return True
    else:
        logging.error(f"[-] Failed to validate lineup. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return False

def fetch_provider_info():
    """Fetch provider information from the TitanTV API."""
    logging.info("[+] Fetching provider information...")
    url = USER_URL.format(user_id=USER_ID)
    response = session.get(url, headers=HEADERS)

    if response.status_code == 200:
        try:
            user_data = response.json()
            provider_info = {
                "providerId": user_data.get("userId", "N/A"),
                "providerName": user_data.get("loginName", "N/A"),
            }
            logging.info(f"[+] Provider information fetched successfully: {provider_info}")
            return provider_info
        except ValueError as e:
            logging.error(f"[-] Error parsing JSON: {e}")
            return None
    else:
        logging.error(f"[-] Failed to fetch provider information. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return None

def fetch_lineup_info():
    """Fetch lineup information from the TitanTV API."""
    logging.info("[+] Fetching lineup information...")
    url = LINEUP_URL.format(user_id=USER_ID)
    response = session.get(url, headers=HEADERS)

    if response.status_code == 200:
        try:
            lineup_data = response.json()
            if "lineups" in lineup_data and lineup_data["lineups"]:
                lineup_info = lineup_data["lineups"][0]
                lineup_info = {
                    "lineupId": lineup_info.get("lineupId"),
                    "lineupName": lineup_info.get("lineupName"),
                    "timeZone": lineup_info.get("timeZone"),
                    "utcOffset": lineup_info.get("utcOffset"),
                    "providerId": lineup_info.get("providerId"),
                    "providerName": lineup_info.get("providerName"),
                }
                if not lineup_info["lineupId"]:
                    logging.error("[-] Missing lineupId in response.")
                    return None
                logging.info(f"[+] Lineup information fetched successfully: {lineup_info}")
                return lineup_info
            else:
                logging.error("[-] No lineups found in response.")
                return None
        except ValueError as e:
            logging.error(f"[-] Error parsing JSON: {e}")
            return None
    else:
        logging.error(f"[-] Failed to fetch lineup information. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return None

def fetch_channel_info(lineup_id):
    """Fetch channel information from the TitanTV API."""
    logging.info("[+] Fetching channel information...")
    url = f"https://titantv.com/api/channel/{USER_ID}/{lineup_id}"
    response = session.get(url, headers=HEADERS)

    if response.status_code == 200:
        try:
            channel_data = response.json()
            if "channels" in channel_data and channel_data["channels"]:
                channels = []
                for channel in channel_data["channels"]:
                    channel_info = {
                        "channelId": channel.get("channelId"),
                        "majorChannel": channel.get("majorChannel"),
                        "minorChannel": channel.get("minorChannel"),
                        "rfChannel": channel.get("rfChannel"),
                        "callSign": channel.get("callSign"),
                        "network": channel.get("network"),
                        "description": channel.get("description"),
                        "hdCapable": channel.get("hdCapable"),
                        "logo": channel.get("logo"),
                    }
                    if not channel_info["channelId"]:
                        logging.error("[-] Missing channelId in response.")
                        return None
                    channels.append(channel_info)
                logging.info(f"[+] Channel information fetched successfully. Found {len(channels)} channels.")
                return channels
            else:
                logging.error("[-] No channels found in response.")
                return None
        except ValueError as e:
            logging.error(f"[-] Error parsing JSON: {e}")
            return None
    else:
        logging.error(f"[-] Failed to fetch channel information. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return None

def fetch_schedule(lineup_id, start_time, duration):
    """Fetches TV schedule for the given lineup and time range."""
    logging.info("[+] Fetching schedule...")
    url = SCHEDULE_URL.format(user_id=USER_ID, lineup_id=lineup_id, start_time=start_time, duration=duration)
    response = session.get(url, headers=HEADERS)

    if response.status_code == 200:
        try:
            schedule_data = response.json()
            logging.info("[+] Schedule data parsed successfully.")
            return schedule_data
        except ValueError as e:
            logging.error(f"[-] Error parsing JSON: {e}")
            return None
    else:
        logging.error(f"[-] Failed to fetch schedule. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return None

def fetch_services():
    """Fetch details about services."""
    logging.info("[+] Fetching services...")
    # Add logic to fetch services from the API
    pass

def fetch_people():
    """Fetch details about people (actors, directors, etc.)."""
    logging.info("[+] Fetching people...")
    # Add logic to fetch people from the API
    pass

def fetch_guide_images():
    """Fetch guide images and associate them with programs."""
    logging.info("[+] Fetching guide images...")
    # Add logic to fetch guide images from the API
    pass