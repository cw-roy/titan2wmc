import logging

def extract_programs(schedule_data):
    """Extracts and processes program data from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    programs = []
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
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
    return programs


def extract_schedule_entries(schedule_data):
    """Extracts and processes schedule entries from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    schedule_entries = []
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
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
    return schedule_entries


def extract_cast_and_crew(schedule_data):
    """Extracts and processes cast and crew from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    cast_and_crew = []
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
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
    return cast_and_crew


def extract_guide_images(schedule_data, channels):
    """Extracts and processes guide images from the fetched schedule and channel data."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    guide_images = []

    # Extracting showCard (program images) from schedule
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
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