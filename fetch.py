import logging
from utils import save_json_to_file  # Import utility function for saving JSON

def fetch_provider_info(session, user_url, headers):
    """Fetch provider information from the TitanTV API."""
    logging.info("[+] Fetching provider information...")
    response = session.get(user_url, headers=headers)

    if response.status_code == 200:
        try:
            user_data = response.json()
            save_json_to_file(user_data, "user.json")  # Save to 'data/user.json'
            return {
                "providerId": user_data.get("userId", "N/A"),
                "providerName": user_data.get("loginName", "N/A"),
            }
        except ValueError as e:
            logging.error(f"[-] Error parsing JSON: {e}")
            return None
    else:
        logging.error(f"[-] Failed to fetch provider information. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return None


def fetch_lineup_info(session, lineup_url, headers):
    """Fetch lineup information from the TitanTV API."""
    logging.info("[+] Fetching lineup information...")
    response = session.get(lineup_url, headers=headers)

    if response.status_code == 200:
        try:
            lineup_data = response.json()
            save_json_to_file(lineup_data, "lineup.json")  # Save to 'data/lineup.json'
            if "lineups" in lineup_data and lineup_data["lineups"]:
                lineup_info = lineup_data["lineups"][0]
                return {
                    "lineupId": lineup_info.get("lineupId"),
                    "lineupName": lineup_info.get("lineupName", "Default Lineup"),
                    "timeZone": lineup_info.get("timeZone"),
                    "utcOffset": lineup_info.get("utcOffset"),
                    "providerId": lineup_info.get("providerId"),
                    "providerName": lineup_info.get("providerName", "Default Provider"),
                }
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


def fetch_channel_info(session, channel_url, headers):
    """Fetch channel information from the TitanTV API."""
    logging.info("[+] Fetching channel information...")
    response = session.get(channel_url, headers=headers)

    if response.status_code == 200:
        try:
            channel_data = response.json()
            save_json_to_file(channel_data, "channels.json")  # Save to 'data/channels.json'
            if "channels" in channel_data and channel_data["channels"]:
                channels = []
                for channel in channel_data["channels"]:
                    if "channelIndex" not in channel:
                        logging.error(f"[-] Missing 'channelIndex' in channel data: {channel}")
                        continue
                    channels.append({
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
                    })
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


def fetch_schedule(session, schedule_url, headers):
    """Fetch TV schedule for the given lineup and time range."""
    logging.info("[+] Fetching schedule...")
    response = session.get(schedule_url, headers=headers)

    if response.status_code == 200:
        try:
            schedule_data = response.json()
            save_json_to_file(schedule_data, "schedule.json")  # Save to 'data/schedule.json'
            return schedule_data
        except ValueError as e:
            logging.error(f"[-] Error parsing JSON: {e}")
            return None
    else:
        logging.error(f"[-] Failed to fetch schedule. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return None