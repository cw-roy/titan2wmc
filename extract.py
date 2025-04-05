import logging

def extract_programs(schedule_data):
    """Extracts and processes program data from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    seen_programs = set()
    programs = []
    
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            if not day.get("events"):
                continue
                
            for event in day["events"]:
                if not event:
                    continue
                    
                program_id = event.get("programId")
                if not program_id or program_id in seen_programs:
                    continue
                    
                seen_programs.add(program_id)
                try:
                    # Map genre to keyword ID
                    genre = event.get("displayGenre", "General")
                    keyword_map = {
                        "News": "k109",
                        "Sports": "k112",
                        "Movies": "k107",
                        "Series": "k104",
                        "Documentary": "k103",
                        "Other": "k113"
                    }
                    keyword_id = keyword_map.get(genre, "k1")
                    
                    program_info = {
                        "programId": program_id,
                        "title": event.get("title", ""),
                        "episodeTitle": event.get("episodeTitle", ""),
                        "description": event.get("description", ""),
                        "shortDescription": event.get("description", "")[:100] if event.get("description") else "",
                        "originalAirDate": event.get("originalAirDate", ""),
                        "keywords": keyword_id,
                        "isSeries": "1" if event.get("programType") == "Series" else "0",
                        "isKids": "1" if event.get("eiAgeCeiling", 0) > 0 else "0",
                        "showCard": event.get("showCard", ""),
                        "seasonNumber": str(event.get("seasonNumber", "")),
                        "episodeNumber": str(event.get("seasonEpisodeNumber", "")),
                        "tvRating": event.get("tvRating", "")
                    }
                    programs.append(program_info)
                except Exception as e:
                    logging.error(f"[-] Error processing program: {e}")
                    continue
    
    return programs


def extract_schedule_entries(schedule_data):
    """Extracts and processes schedule entries from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    schedule_entries = []
    
    for channel in schedule_data.get("channels", []):
        service_id = f"s{channel.get('channelIndex', '')}"
        for day in channel.get("days", []):
            if not day.get("events"):
                continue
                
            for event in day["events"]:
                if not event:
                    continue
                    
                try:
                    if all(key in event for key in ["programId", "startTime", "duration"]):
                        schedule_entry = {
                            "service": service_id,
                            "program": str(event["programId"]),
                            "startTime": event["startTime"],
                            "duration": str(event["duration"]),
                            "isCC": "1" if event.get("isCC") else "0",
                            "audioFormat": "2"  # Default to stereo
                        }
                        schedule_entries.append(schedule_entry)
                except Exception as e:
                    logging.error(f"[-] Error processing schedule entry: {e}")
                    continue
    
    return schedule_entries

def extract_cast_and_crew(schedule_data):
    """Extracts and processes cast and crew information from the fetched schedule."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    seen_people = set()
    cast_and_crew = []
    
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                for person in event.get("castAndCrew", []):
                    person_id = person.get("personId")
                    if person_id and str(person_id) not in seen_people:
                        seen_people.add(str(person_id))
                        try:
                            cast_and_crew.append({
                                "personId": person_id,
                                "name": person.get("name", ""),
                                "role": person.get("role", ""),
                                "character": person.get("character", ""),
                                "isCast": person.get("isCast", False),
                                "programId": event.get("programId", "")
                            })
                        except Exception as e:
                            logging.error(f"[-] Error processing cast/crew member: {e}")
                            continue
    return cast_and_crew

def extract_series_info(schedule_data):
    """Extracts series information from schedule data."""
    if not schedule_data or "channels" not in schedule_data:
        logging.error("[-] No valid schedule data found.")
        return []

    seen_series = set()
    series_info = []
    
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                if event.get("programType") == "Series":
                    series_id = event.get("parentProgramId")
                    if series_id and series_id not in seen_series:
                        seen_series.add(series_id)
                        try:
                            series_info.append({
                                "id": f"si{series_id}",
                                "uid": f"!Series!{event.get('title', '')}",
                                "title": event.get("title", ""),
                                "shortTitle": event.get("title", ""),
                                "description": event.get("seriesDescription", ""),
                                "shortDescription": event.get("seriesDescription", "")[:100] if event.get("seriesDescription") else "",
                                "startAirdate": event.get("originalAirDate", "")
                            })
                        except Exception as e:
                            logging.error(f"[-] Error processing series info: {e}")
                            continue
    return series_info

def extract_guide_images(schedule_data, channels):
    """Extracts guide images from schedule and channel data."""
    guide_images = []
    seen_images = set()

    # Extract channel logos
    for channel in channels:
        logo = channel.get("logo", "")
        channel_id = channel.get("channelIndex")
        if logo and channel_id and logo not in seen_images:
            seen_images.add(logo)
            guide_images.append({
                "id": f"i{channel_id}",
                "uid": f"!Image!{channel.get('callSign', '')}",
                "imageUrl": logo
            })

    # Extract program show cards
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                show_card = event.get("showCard", "")
                program_id = event.get("programId")
                if show_card and program_id and show_card not in seen_images:
                    seen_images.add(show_card)
                    guide_images.append({
                        "id": f"i{program_id}",
                        "uid": f"!Image!{program_id}",
                        "imageUrl": show_card
                    })

    return guide_images