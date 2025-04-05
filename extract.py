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
                        "originalAirDate": event.get("originalAirDate", "N/A"),
                        "keywords": event.get("displayGenre", "N/A"),
                        "isSeries": "1" if event.get("isSeries", False) else "0",
                        "isKids": "1" if event.get("isKids", False) else "0",
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
        service_id = f"s{channel.get('channelIndex', 'unknown')}"
        for day in channel.get("days", []):
            for event in day.get("events", []):
                try:
                    schedule_entry = {
                        "service": service_id,
                        "program": event.get("programId", "N/A"),
                        "startTime": event.get("startTime", "N/A"),
                        "duration": event.get("duration", "N/A"),
                        "isCC": "1" if event.get("isCC", False) else "0",
                        "audioFormat": "2" if event.get("isStereo", False) else "1",
                    }
                    schedule_entries.append(schedule_entry)
                except KeyError as e:
                    logging.error(f"[-] Missing expected key: {e}")
    return schedule_entries


def extract_people_and_roles(schedule_data):
    """Extracts and processes people and their roles from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return [], []

    people = []
    roles = []
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                for person in event.get("castAndCrew", []):
                    try:
                        person_info = {
                            "personId": person.get("personId", "N/A"),
                            "name": person.get("name", "N/A"),
                        }
                        role_info = {
                            "personId": person.get("personId", "N/A"),
                            "role": person.get("role", "N/A"),
                            "programId": event.get("programId", "N/A"),
                        }
                        people.append(person_info)
                        roles.append(role_info)
                    except KeyError as e:
                        logging.error(f"[-] Missing expected key: {e}")
    return people, roles


def extract_guide_images(schedule_data, channels):
    """Extracts and processes guide images from the fetched schedule and channel data."""
    guide_images = []

    # Extracting showCard (program images) from schedule
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                show_card = event.get("showCard", "")
                if show_card:
                    guide_images.append({
                        "id": f"i{event.get('programId', 'unknown')}",
                        "uid": f"!Image!{event.get('programId', 'unknown')}",
                        "imageUrl": show_card,
                    })

    # Extracting logo (station logos) from channels
    for channel in channels:
        logo = channel.get("logo", "")
        if logo:
            guide_images.append({
                "id": f"i{channel['channelIndex']}",
                "uid": f"!Image!{channel['callSign']}",
                "imageUrl": logo,
            })

    return guide_images


def extract_cast_and_crew(schedule_data):
    """Extracts and processes cast and crew information from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    cast_and_crew = []
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                for person in event.get("castAndCrew", []):
                    try:
                        cast_and_crew.append({
                            "personId": person.get("personId", "N/A"),
                            "name": person.get("name", "N/A"),
                            "role": person.get("role", "N/A"),
                            "programId": event.get("programId", "N/A"),
                        })
                    except KeyError as e:
                        logging.error(f"[-] Missing expected key: {e}")
    return cast_and_crew