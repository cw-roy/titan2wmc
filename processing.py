import logging
from lxml import etree  # type: ignore

def safe_str(value):
    """Convert value to string, handling None values."""
    return str(value) if value is not None else ""

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

def add_services_section(with_section, channels):
    """Add Services section with channel data."""
    services = etree.SubElement(with_section, "Services")
    for channel in channels:
        if channel.get("callSign") and channel.get("channelIndex"):
            etree.SubElement(services, "Service", attrib={
                "id": f"s{safe_str(channel['channelIndex'])}",
                "uid": f"!Service!{safe_str(channel['callSign'])}",
                "name": safe_str(channel.get("network", "")),
                "callSign": safe_str(channel['callSign']),
                "affiliate": f"!Affiliate!{safe_str(channel.get('network', ''))}"
            })

def add_schedule_entries_section(with_section, schedule_data, processed_data):
    """Add ScheduleEntries section with program schedule data."""
    schedule_entries_dict = {}
    
    for entry in processed_data["schedule_entries"]:
        service_id = entry.get("service")
        if not service_id:
            continue
            
        if service_id not in schedule_entries_dict:
            schedule_entries_dict[service_id] = etree.SubElement(
                with_section, 
                "ScheduleEntries",
                attrib={"service": service_id}
            )
            
        if entry.get("program") and entry.get("startTime"):
            etree.SubElement(schedule_entries_dict[service_id], "ScheduleEntry", attrib={
                "program": safe_str(entry["program"]),
                "startTime": safe_str(entry["startTime"]),
                "duration": safe_str(entry["duration"]),
                "isCC": safe_str(entry.get("isCC", "0")),
                "audioFormat": safe_str(entry.get("audioFormat", "2"))
            })

def add_lineups_section(with_section, lineup_info, channels):
    """Add Lineups section with channel mappings."""
    lineups = etree.SubElement(with_section, "Lineups")
    lineup = etree.SubElement(lineups, "Lineup", attrib={
        "id": "l1",  # Always "l1" as per the documentation
        "uid": f"!Lineup!{safe_str(lineup_info['lineupName'])}",
        "name": safe_str(lineup_info["lineupName"])
    })
    
    channels_element = etree.SubElement(lineup, "channels")
    for channel in channels:
        if channel.get("channelIndex"):
            major_channel = safe_str(channel.get("majorChannel", -1))
            minor_channel = safe_str(channel.get("minorChannel", 0))
            channel_uid = f"!Channel!{safe_str(lineup_info['lineupName'])}!{major_channel}.{minor_channel}"
            service_id = f"s{safe_str(channel['channelIndex'])}"
            match_name = safe_str(channel.get("callSign", ""))

            etree.SubElement(channels_element, "Channel", attrib={
                "uid": channel_uid,
                "lineup": "l1",
                "service": service_id,
                "number": f"{major_channel}.{minor_channel}",
                "matchName": match_name
            })

def add_people_section(with_section, cast_and_crew):
    """Add People section with cast and crew data."""
    people = etree.SubElement(with_section, "People")
    for person in cast_and_crew:
        if person.get("name"):
            etree.SubElement(people, "Person", attrib={
                "id": f"p{safe_str(person['personId'])}",
                "name": safe_str(person['name']),
                "uid": f"!Person!{safe_str(person['name'])}"
            })

def add_series_infos_section(with_section, series_info):
    """Add SeriesInfos section with series data."""
    series_infos = etree.SubElement(with_section, "SeriesInfos")
    for series in series_info:
        etree.SubElement(series_infos, "SeriesInfo", attrib={
            "id": safe_str(series["id"]),
            "uid": safe_str(series["uid"]),
            "title": safe_str(series["title"]),
            "shortTitle": safe_str(series["shortTitle"]),
            "description": safe_str(series["description"]),
            "shortDescription": safe_str(series["shortDescription"]),
            "startAirdate": safe_str(series["startAirdate"])
        })

def add_programs_section(with_section, programs):
    """Add Programs section with program data."""
    programs_section = etree.SubElement(with_section, "Programs")
    for program in programs:
        etree.SubElement(programs_section, "Program", attrib={
            "id": safe_str(program["programId"]),
            "uid": f"!Program!{safe_str(program['programId'])}",
            "title": safe_str(program["title"]),
            "description": safe_str(program["description"]),
            "shortDescription": safe_str(program["shortDescription"]),
            "episodeTitle": safe_str(program["episodeTitle"]),
            "originalAirdate": safe_str(program["originalAirDate"]),
            "keywords": safe_str(program["keywords"]),
            "isSeries": safe_str(program["isSeries"]),
            "isKids": safe_str(program["isKids"])
        })

def generate_mxf(provider_info, lineup_info, channels, schedule_data, processed_data):
    """Generate the .mxf XML structure."""
    root = etree.Element("MXF", nsmap={
        "sql": "urn:schemas-microsoft-com:XML-sql",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance"
    })

    # Add Assembly Section
    etree.SubElement(root, "Assembly", attrib={
        "name": "mcepg",
        "version": "6.0.6000.0",
        "cultureInfo": "",
        "publicKey": "0024000004800000940000000602000000240000525341310004000001000100B5FC90E7027F67871E773A8FDE8938C81DD402BA65B9201D60593E96C492651E889CC13F1415EBB53FAC1131AE0BD333C5EE6021672D9718EA31A8AEBD0DA0072F25D87DBA6FC90FFD598ED4DA35E44C398C454307E8E33B8426143DAEC9F596836F97C8F74750E5975C64E2189F45DEF46B2A2B1247ADC3652BF5C308055DA9"
    })

    # Add Providers section
    providers = etree.SubElement(root, "Providers")
    etree.SubElement(providers, "Provider", attrib={
        "id": safe_str(provider_info.get("providerId")),
        "name": safe_str(provider_info.get("providerName")),
        "displayName": safe_str(provider_info.get("providerName")),
        "copyright": "© 2025 TitanTV Inc. All Rights Reserved."
    })

    # Create With section
    with_section = etree.SubElement(root, "With", attrib={
        "provider": safe_str(provider_info.get("providerId"))
    })

    # Add People section
    add_people_section(with_section, processed_data["cast_and_crew"])

    # Add SeriesInfos section
    add_series_infos_section(with_section, processed_data["series_info"])

    # Add Programs section
    add_programs_section(with_section, processed_data["programs"])

    # Convert to string and pretty-print
    pretty_xml = etree.tostring(root, pretty_print=True, encoding="unicode")

    return pretty_xml