import logging
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString


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