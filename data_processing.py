import logging

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

def summarize_listings(listings):
    """Summarizes the extracted listings for logging or reporting."""
    if not listings:
        logging.info("[+] No listings to summarize.")
        return

    logging.info(f"[+] Total Listings: {len(listings)}")
    for listing in listings[:5]:  # Log the first 5 listings as a preview
        logging.info(f"    - {listing['title']} ({listing['start_time']} - {listing['end_time']})")

def save_listings_to_file(listings, filename="listings.json"):
    """Saves the extracted listings to a JSON file."""
    import json

    try:
        with open(filename, "w") as f:
            json.dump(listings, f, indent=4)
        logging.info(f"[+] Listings saved to {filename}.")
    except IOError as e:
        logging.error(f"[-] Failed to save listings to file: {e}")