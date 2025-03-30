import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

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
            logging.info(f"[+] Provider Info: {provider_info}")
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

            # Check if the "lineups" key is present and it's a non-empty list
            if "lineups" in lineup_data and lineup_data["lineups"]:
                lineup_info = lineup_data["lineups"][0]  # Take the first lineup if available
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

            # Check if the "channels" key is present and it's a non-empty list
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

def extract_programs(schedule_data):
    """Extracts and processes program data from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    programs = []
    
    # Ensure the response has 'channels'
    if "channels" in schedule_data:
        for channel in schedule_data["channels"]:
            if "days" in channel:
                for day in channel["days"]:
                    if "events" in day:
                        for event in day["events"]:
                            try:
                                program_info = {
                                    "programId": event.get("programId", "N/A"),
                                    "title": event.get("title", "N/A"),
                                    "episodeTitle": event.get("episodeTitle", "N/A"),
                                    "description": event.get("description", "N/A"),
                                    "programType": event.get("programType", "N/A"),
                                    "year": event.get("year", "N/A"),
                                    "originalAirDate": event.get("originalAirDate", "N/A"),
                                    "tvRating": event.get("tvRating", "N/A"),
                                    "mpaaRating": event.get("mpaaRating", "N/A"),
                                    "displayGenre": event.get("displayGenre", "N/A"),
                                    "starRating": event.get("starRating", "N/A"),
                                    "showCard": event.get("showCard", ""),
                                }
                                programs.append(program_info)
                            except KeyError as e:
                                logging.error(f"[-] Missing expected key: {e}")
    else:
        logging.error("[-] No 'channels' found in schedule data.")
    
    return programs

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

def extract_schedule_entries(schedule_data):
    """Extracts and processes schedule entries from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    schedule_entries = []
    
    # Ensure the response has 'channels'
    if "channels" in schedule_data:
        for channel in schedule_data["channels"]:
            if "days" in channel:
                for day in channel["days"]:
                    if "events" in day:
                        for event in day["events"]:
                            try:
                                schedule_entry = {
                                    "eventId": event.get("eventId", "N/A"),
                                    "startTime": event.get("startTime", "N/A"),
                                    "endTime": event.get("endTime", "N/A"),
                                    "duration": event.get("duration", "N/A"),
                                    "newRepeat": event.get("newRepeat", "N/A"),
                                    "liveTapeReplay": event.get("liveTapeReplay", "N/A"),
                                    "textLanguage": event.get("textLanguage", "N/A"),
                                    "seriesDescription": event.get("seriesDescription", "N/A"),
                                    "seasonNumber": event.get("seasonNumber", "N/A"),
                                    "seasonEpisodeNumber": event.get("seasonEpisodeNumber", "N/A"),
                                }
                                schedule_entries.append(schedule_entry)
                            except KeyError as e:
                                logging.error(f"[-] Missing expected key: {e}")
    else:
        logging.error("[-] No 'channels' found in schedule data.")
    
    return schedule_entries

def extract_cast_and_crew(schedule_data):
    """Extracts and processes cast and crew from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    cast_and_crew = []
    
    # Ensure the response has 'channels'
    if "channels" in schedule_data:
        for channel in schedule_data["channels"]:
            if "days" in channel:
                for day in channel["days"]:
                    if "events" in day:
                        for event in day["events"]:
                            try:
                                # Check for cast and crew in each event
                                if "castAndCrew" in event:
                                    for person in event["castAndCrew"]:
                                        person_info = {
                                            "personId": person.get("personId", "N/A"),
                                            "name": person.get("name", "N/A"),
                                            "role": person.get("role", "N/A"),
                                            "character": person.get("character", "N/A"),
                                        }
                                        cast_and_crew.append(person_info)
                            except KeyError as e:
                                logging.error(f"[-] Missing expected key: {e}")
    else:
        logging.error("[-] No 'channels' found in schedule data.")
    
    return cast_and_crew

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
if __name__ == "__main__":
    try:
        logging.info("[+] Start run...")
        session = login()
        if session:
            logging.info("[+] Ready to proceed with user and provider validation.")
            
            # Validate user
            if validate_user():
                # Fetch provider information after validating user
                provider_info = fetch_provider_info()
                if not provider_info:
                    logging.error("[-] Failed to fetch provider information. Exiting.")
                    exit(1)
                
                # Log provider information
                logging.info(f"[+] Using provider: {provider_info['providerName']} (ID: {provider_info['providerId']})")
                
                # Fetch lineup information after fetching provider info
                lineup_info = fetch_lineup_info()
                if not lineup_info:
                    logging.error("[-] Failed to fetch lineup information. Exiting.")
                    exit(1)
                
                # Log lineup information
                logging.info(f"[+] Using lineup: {lineup_info['lineupName']} (ID: {lineup_info['lineupId']})")
                
                # Fetch channel information
                channels = fetch_channel_info(lineup_info['lineupId'])
                if not channels:
                    logging.error("[-] Failed to fetch channel information. Exiting.")
                    exit(1)

                # Log channel information
                logging.info(f"[+] Found {len(channels)} channels.")
                for channel in channels:
                    logging.info(f"Channel {channel['channelId']}: {channel['callSign']} - {channel['network']}")

                # Validate provider lineup
                if validate_lineup():
                    # Use lineupId dynamically for fetching schedule
                    lineup_id = lineup_info.get("lineupId", "default_lineup_id")
                    start_time = get_current_start_time()  # Use dynamic current start time
                    duration = "60"  # Example duration in minutes. Adjust as needed.
                    
                    logging.info(f"[+] Fetching schedule for lineup ID: {lineup_id}, start time: {start_time}, duration: {duration} minutes.")
                    
                    # Fetch the schedule data             
                    schedule_data = fetch_schedule(lineup_id, start_time, duration)
                    if schedule_data:
                        # Extract and log the TV listings
                        listings = extract_listings(schedule_data)
                        if listings:
                            logging.info(f"[+] Found {len(listings)} listings.")
                        else:
                            logging.error("[-] No listings found.")
                        
                        # Extract and log the programs
                        programs = extract_programs(schedule_data)
                        if programs:
                            logging.info(f"[+] Found {len(programs)} programs.")
                            for program in programs:
                                logging.info(f"Program {program['programId']}: {program['title']} - {program['episodeTitle']} ({program['programType']})")
                        else:
                            logging.error("[-] No programs found.")
                        
                        # Extract and log the schedule entries
                        schedule_entries = extract_schedule_entries(schedule_data)
                        if schedule_entries:
                            logging.info(f"[+] Found {len(schedule_entries)} schedule entries.")
                            for entry in schedule_entries:
                                logging.info(f"Event {entry['eventId']}: {entry['startTime']} - {entry['endTime']} (Duration: {entry['duration']} minutes)")
                        else:
                            logging.error("[-] No schedule entries found.")
                        
                        # Extract and log the cast and crew
                        cast_and_crew = extract_cast_and_crew(schedule_data)
                        if cast_and_crew:
                            logging.info(f"[+] Found {len(cast_and_crew)} cast and crew members.")
                            for person in cast_and_crew:
                                logging.info(f"Person {person['personId']}: {person['name']} - {person['role']} as {person['character']}")
                        else:
                            logging.error("[-] No cast and crew found.")
                else:
                    logging.error("[-] Provider lineup validation failed.")
            else:
                logging.error("[-] User validation failed.")
                
        logging.info("[+] End of run.")
    finally:       
        if session:
            session.close()
            logging.info("[+] Session closed.")
