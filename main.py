import json
import requests
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

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

DEFAULT_DURATION = "300"

# Utility Functions
def save_json_to_file(data, filename):
    """Save JSON data to a file."""
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        logging.info(f"[+] Saved JSON data to {filename}")
    except Exception as e:
        logging.error(f"[-] Failed to save JSON to {filename}: {e}")

def load_json(filename):
    """Load JSON data from a file."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
        logging.info(f"[+] Loaded JSON data from {filename}")
        return data
    except Exception as e:
        logging.error(f"[-] Failed to load JSON from {filename}: {e}")
        return None

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
            save_json_to_file(user_data, "data/user.json")  # Save response to user.json
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
            save_json_to_file(lineup_data, "data/lineup.json")  # Save response to lineup.json

            # Check if the "lineups" key is present and it's a non-empty list
            if "lineups" in lineup_data and lineup_data["lineups"]:
                lineup_info = lineup_data["lineups"][0]  # Take the first lineup if available
                lineup_info = {
                    "lineupId": lineup_info.get("lineupId"),
                    "lineupName": lineup_info.get("lineupName", "Default Lineup"),
                    "timeZone": lineup_info.get("timeZone"),
                    "utcOffset": lineup_info.get("utcOffset"),
                    "providerId": lineup_info.get("providerId"),
                    "providerName": lineup_info.get("providerName", "Default Provider"),
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
            save_json_to_file(channel_data, "data/channels.json")  # Save response to channels.json

            # Check if the "channels" key is present and it's a non-empty list
            if "channels" in channel_data and channel_data["channels"]:
                channels = []
                for channel in channel_data["channels"]:
                    if "channelIndex" not in channel:
                        logging.error(f"[-] Missing 'channelIndex' in channel data: {channel}")
                        continue  # Skip this channel if 'channelIndex' is missing

                    channel_info = {
                        "channelId": channel.get("channelId"),
                        "channelIndex": channel.get("channelIndex"),
                        "majorChannel": channel.get("majorChannel"),
                        "minorChannel": channel.get("minorChannel"),
                        "rfChannel": channel.get("rfChannel"),
                        "callSign": channel.get("callSign"),
                        "network": channel.get("network"),
                        "description": channel.get("description"),
                        "hdCapable": channel.get("hdCapable"),
                        "logo": channel.get("logo"),
                    }

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
                save_json_to_file(schedule_data, "data/schedule.json")  # Save response to schedule.json
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

def extract_guide_images(schedule_data, channels):
    """Extracts and processes guide images from the fetched schedule and channel data."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    guide_images = []
    
    # Extracting showCard (program images) from schedule
    if "channels" in schedule_data:
        for channel in schedule_data["channels"]:
            if "days" in channel:
                for day in channel["days"]:
                    if "events" in day:
                        for event in day["events"]:
                            try:
                                show_card = event.get("showCard", "")
                                if show_card:
                                    guide_images.append({
                                        "showCard": show_card,
                                        "channelId": channel.get("channelId", "N/A"),
                                        "eventId": event.get("eventId", "N/A"),
                                    })
                            except KeyError as e:
                                logging.error(f"[-] Missing expected key: {e}")
    
    # Extracting logo (station logos) from channels
    for channel in channels:
        try:
            logo = channel.get("logo", "")
            if logo:
                guide_images.append({
                    "logo": logo,
                    "channelId": channel.get("channelId", "N/A"),
                })
        except KeyError as e:
            logging.error(f"[-] Missing expected key: {e}")
    
    return guide_images


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

def generate_mxf(provider_info, lineup_info, channels, schedule_data):
    """Generate the .mxf XML structure."""
    root = ET.Element("MXF", attrib={
        "xmlns:sql": "urn:schemas-microsoft-com:XML-sql",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
    })

    # Add Assembly Section
    assembly = ET.SubElement(root, "Assembly", attrib={
        "name": "mcepg",
        "version": "6.0.6000.0",
        "cultureInfo": "",
        "publicKey": "0024000004800000940000000602000000240000525341310004000001000100B5FC90E7027F67871E773A8FDE8938C81DD402BA65B9201D60593E96C492651E889CC13F1415EBB53FAC1131AE0BD333C5EE6021672D9718EA31A8AEBD0DA0072F25D87DBA6FC90FFD598ED4DA35E44C398C454307E8E33B8426143DAEC9F596836F97C8F74750E5975C64E2189F45DEF46B2A2B1247ADC3652BF5C308055DA9"
    })
    namespace = ET.SubElement(assembly, "NameSpace", attrib={"name": "Microsoft.MediaCenter.Guide"})
    for type_name in [
        "Lineup", "Channel", "Service", "ScheduleEntry", "Program", "Keyword",
        "KeywordGroup", "Person", "ActorRole", "DirectorRole", "WriterRole",
        "HostRole", "GuestActorRole", "ProducerRole", "GuideImage", "Affiliate",
        "SeriesInfo", "Season"
    ]:
        ET.SubElement(namespace, "Type", attrib={"name": type_name})

    # Add Providers
    providers = ET.SubElement(root, "Providers")
    ET.SubElement(providers, "Provider", attrib={
        "id": str(lineup_info["providerId"]),
        "name": lineup_info["providerName"],
        "displayName": lineup_info["providerName"],
        "copyright": "© 2025 TitanTV Inc. All Rights Reserved."
    })

    # Add Keywords and KeywordGroups
    keywords = ET.SubElement(root, "Keywords")
    keyword_groups = ET.SubElement(root, "KeywordGroups")
    ET.SubElement(keywords, "Keyword", attrib={"id": "k1", "word": "General"})
    ET.SubElement(keyword_groups, "KeywordGroup", attrib={
        "uid": "!KeywordGroup!k1",
        "groupName": "General",
        "keywords": "k1,k2,k3"
    })

    # Add GuideImages
    guide_images = ET.SubElement(root, "GuideImages")
    for channel in channels:
        if channel.get("logo"):
            ET.SubElement(guide_images, "GuideImage", attrib={
                "id": f"i{channel['channelIndex']}",
                "uid": f"!Image!{channel['callSign']}",
                "imageUrl": channel["logo"]
            })

    # Add People and Roles
    people = ET.SubElement(root, "People")
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                for person in event.get("castAndCrew", []):
                    person_name = person.get("name")
                    if not person_name:
                        continue
                    person_id = person.get("id", person_name.replace(" ", "_"))
                    ET.SubElement(people, "Person", attrib={
                        "id": f"p{person_id}",
                        "name": person_name,
                        "uid": f"!Person!{person_name}"
                    })

    # Add SeriesInfos and Seasons
    series_infos = ET.SubElement(root, "SeriesInfos")
    seasons = ET.SubElement(root, "Seasons")
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                if "seriesDescription" in event:
                    series_id = f"si{event['programId']}"
                    ET.SubElement(series_infos, "SeriesInfo", attrib={
                        "id": series_id,
                        "uid": f"!Series!{event['seriesDescription']}",
                        "title": event["seriesDescription"]
                    })
                    ET.SubElement(seasons, "Season", attrib={
                        "id": f"sn{event['programId']}",
                        "uid": f"!Season!{event['programId']}",
                        "series": series_id
                    })

    # Add Programs
    programs = ET.SubElement(root, "Programs")
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                ET.SubElement(programs, "Program", attrib={
                    "id": str(event["programId"]),
                    "uid": f"!Program!{event['programId']}",
                    "title": event["title"],
                    "description": event["description"],
                    "episodeTitle": event.get("episodeTitle", ""),
                    "originalAirdate": event.get("originalAirDate", ""),
                    "keywords": event.get("displayGenre", "")
                })

    # Add ScheduleEntries
    for channel in schedule_data.get("channels", []):
        service_id = f"s{channel.get('channelIndex', 'unknown')}"  # Use 'unknown' if channelIndex is missing
        schedule_entries = ET.SubElement(root, "ScheduleEntries", attrib={"service": service_id})
        for day in channel.get("days", []):
            for event in day.get("events", []):
                ET.SubElement(schedule_entries, "ScheduleEntry", attrib={
                    "program": str(event["programId"]),
                    "startTime": event["startTime"],
                    "duration": str(event["duration"]),
                    "isCC": "1" if event.get("isHD", False) else "0",
                    "audioFormat": "2"  # Example value, adjust as needed
                })

    # Convert to string and pretty-print
    raw_xml = ET.tostring(root, encoding="unicode", method="xml")
    pretty_xml = parseString(raw_xml).toprettyxml(indent="  ")

    return pretty_xml

if __name__ == "__main__":
    try:
        logging.info("[+] Start run...")
        session = requests.Session()

        # Fetch provider information
        provider_info = fetch_provider_info()
        if not provider_info:
            logging.error("[-] Failed to fetch provider information. Exiting.")
            exit(1)

        # Fetch lineup information
        lineup_info = fetch_lineup_info()
        if not lineup_info:
            logging.error("[-] Failed to fetch lineup information. Exiting.")
            exit(1)

        # Fetch channel information
        channels = fetch_channel_info(lineup_info["lineupId"])
        if not channels:
            logging.error("[-] Failed to fetch channel information. Exiting.")
            exit(1)

        # Fetch schedule
        start_time = get_current_start_time()
        duration = DEFAULT_DURATION
        schedule_data = fetch_schedule(lineup_info["lineupId"], start_time, duration)
        if not schedule_data:
            logging.error("[-] Failed to fetch schedule. Exiting.")
            exit(1)

        # Generate the .mxf content
        mxf_content = generate_mxf(provider_info, lineup_info, channels, schedule_data)

        # Save to output.mxf
        with open("output.mxf", "w", encoding="utf-8") as file:
            file.write(mxf_content)
        logging.info("[+] Successfully generated output.mxf.")
    finally:
        if session:
            session.close()
            logging.info("[+] Session closed.")
