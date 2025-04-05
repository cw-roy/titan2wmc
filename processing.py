import logging
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from extract import extract_programs, extract_schedule_entries, extract_cast_and_crew, extract_guide_images

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
    services = ET.SubElement(with_section, "Services")
    for channel in channels:
        if channel.get("callSign"):
            ET.SubElement(services, "Service", attrib={
                "id": f"s{safe_str(channel['channelIndex'])}",
                "uid": f"!Service!{safe_str(channel['callSign'])}",
                "name": safe_str(channel.get("network", "")),
                "callSign": safe_str(channel['callSign'])
            })

def add_schedule_entries_section(with_section, schedule_data):
    """Add ScheduleEntries section with program schedule data."""
    schedule_entries_dict = {}
    
    # First, group entries by service
    for entry in extract_schedule_entries(schedule_data):
        service_id = entry.get("service")
        if service_id:
            if service_id not in schedule_entries_dict:
                schedule_entries_dict[service_id] = []
            schedule_entries_dict[service_id].append(entry)

    # Then create ScheduleEntries sections for each service
    for service_id, entries in schedule_entries_dict.items():
        schedule_entries = ET.SubElement(with_section, "ScheduleEntries", 
                                       attrib={"service": service_id})
        for entry in entries:
            ET.SubElement(schedule_entries, "ScheduleEntry", attrib={
                "program": safe_str(entry.get("program")),
                "startTime": safe_str(entry.get("startTime")),
                "duration": safe_str(entry.get("duration")),
                "isCC": safe_str(entry.get("isCC", "0")),
                "audioFormat": safe_str(entry.get("audioFormat", "2"))
            })

def generate_mxf(provider_info, lineup_info, channels, schedule_data):
    """Generate the .mxf XML structure."""
    root = ET.Element("MXF", attrib={
        "xmlns:sql": "urn:schemas-microsoft-com:XML-sql",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
    })

    # Add Assembly Section
    assembly_mcepg = ET.SubElement(root, "Assembly", attrib={
        "name": "mcepg",
        "version": "6.0.6000.0",
        "cultureInfo": "",
        "publicKey": "0024000004800000940000000602000000240000525341310004000001000100B5FC90E7027F67871E773A8FDE8938C81DD402BA65B9201D60593E96C492651E889CC13F1415EBB53FAC1131AE0BD333C5EE6021672D9718EA31A8AEBD0DA0072F25D87DBA6FC90FFD598ED4DA35E44C398C454307E8E33B8426143DAEC9F596836F97C8F74750E5975C64E2189F45DEF46B2A2B1247ADC3652BF5C308055DA9"
    })

    # Add mcepg namespace with proper Type definitions
    namespace = ET.SubElement(assembly_mcepg, "NameSpace", attrib={"name": "Microsoft.MediaCenter.Guide"})
    type_definitions = [
        ("Lineup", {}),
        ("Channel", {"parentFieldName": "lineup"}),
        ("Service", {}),
        ("ScheduleEntry", {"groupName": "ScheduleEntries"}),
        ("Program", {}),
        ("Keyword", {}),
        ("KeywordGroup", {}),
        ("Person", {"groupName": "People"}),
        ("ActorRole", {"parentFieldName": "program"}),
        ("DirectorRole", {"parentFieldName": "program"}),
        ("WriterRole", {"parentFieldName": "program"}),
        ("HostRole", {"parentFieldName": "program"}),
        ("GuestActorRole", {"parentFieldName": "program"}),
        ("ProducerRole", {"parentFieldName": "program"}),
        ("GuideImage", {}),
        ("Affiliate", {}),
        ("SeriesInfo", {}),
        ("Season", {})
    ]
    
    for type_name, attributes in type_definitions:
        attribs = {"name": type_name}
        attribs.update(attributes)
        ET.SubElement(namespace, "Type", attrib=attribs)

    # Add mcstore Assembly
    assembly_mcstore = ET.SubElement(root, "Assembly", attrib={
        "name": "mcstore",
        "version": "6.0.6000.0",
        "cultureInfo": "",
        "publicKey": "0024000004800000940000000602000000240000525341310004000001000100B5FC90E7027F67871E773A8FDE8938C81DD402BA65B9201D60593E96C492651E889CC13F1415EBB53FAC1131AE0BD333C5EE6021672D9718EA31A8AEBD0DA0072F25D87DBA6FC90FFD598ED4DA35E44C398C454307E8E33B8426143DAEC9F596836F97C8F74750E5975C64E2189F45DEF46B2A2B1247ADC3652BF5C308055DA9"
    })

    # Add mcstore namespace
    mcstore_ns = ET.SubElement(assembly_mcstore, "NameSpace", attrib={"name": "Microsoft.MediaCenter.Store"})
    ET.SubElement(mcstore_ns, "Type", attrib={"name": "Provider"})
    ET.SubElement(mcstore_ns, "Type", attrib={"name": "UId", "parentFieldName": "target"})

    # Add Providers section
    providers = ET.SubElement(root, "Providers")
    ET.SubElement(providers, "Provider", attrib={
        "id": safe_str(provider_info.get("providerId")),
        "name": safe_str(provider_info.get("providerName")),
        "displayName": safe_str(provider_info.get("providerName")),
        "copyright": "© 2025 TitanTV Inc. All Rights Reserved."
    })

    # Create With section
    with_section = ET.SubElement(root, "With", attrib={
        "provider": safe_str(provider_info.get("providerId"))
    })

    # Add Keywords section
    keywords = ET.SubElement(with_section, "Keywords")
    keyword_data = [
        ("k1", "General"),
        ("k100", "All"),
        ("k101", "Action/Adventure"),
        ("k102", "Comedy"),
        ("k103", "Documentary/Bio"),
        ("k104", "Drama"),
        ("k105", "Educational"),
        ("k106", "Family/Children"),
        ("k107", "Movies"),
        ("k108", "Music"),
        ("k109", "News"),
        ("k110", "Sci-Fi/Fantasy"),
        ("k111", "Soap"),
        ("k112", "Sports"),
        ("k113", "Other")
    ]
    for k_id, word in keyword_data:
        ET.SubElement(keywords, "Keyword", attrib={"id": k_id, "word": word})

    # Add KeywordGroups section
    keyword_groups = ET.SubElement(with_section, "KeywordGroups")
    ET.SubElement(keyword_groups, "KeywordGroup", attrib={
        "uid": "!KeywordGroup!k1",
        "groupName": "General",
        "keywords": "k100,k101,k102,k103,k104,k105,k106,k107,k108,k109,k110,k111,k112,k113"
    })

    # Add GuideImages section
    guide_images = ET.SubElement(with_section, "GuideImages")
    for channel in channels:
        if channel.get("logo"):
            ET.SubElement(guide_images, "GuideImage", attrib={
                "id": f"i{safe_str(channel['channelIndex'])}",
                "uid": f"!Image!{safe_str(channel['callSign'])}",
                "imageUrl": safe_str(channel['logo'])
            })

    # Add People section
    people = ET.SubElement(with_section, "People")
    cast_and_crew = extract_cast_and_crew(schedule_data)
    for person in cast_and_crew:
        if person.get("name"):
            ET.SubElement(people, "Person", attrib={
                "id": f"p{safe_str(person['personId'])}",
                "name": safe_str(person['name']),
                "uid": f"!Person!{safe_str(person['name'])}"
            })

    # Add SeriesInfos section
    ET.SubElement(with_section, "SeriesInfos")

    # Add Seasons section
    ET.SubElement(with_section, "Seasons")

    # Add Programs section
    programs = ET.SubElement(with_section, "Programs")
    for program in extract_programs(schedule_data):
        if program.get("title"):
            ET.SubElement(programs, "Program", attrib={
                "id": safe_str(program["programId"]),
                "uid": f"!Program!{safe_str(program['programId'])}",
                "title": safe_str(program["title"]),
                "description": safe_str(program["description"]),
                "originalAirdate": safe_str(program["originalAirDate"]),
                "keywords": safe_str(program["keywords"]),
                "isSeries": safe_str(program["isSeries"]),
                "isKids": safe_str(program["isKids"])
            })

    # Add Affiliates section
    ET.SubElement(with_section, "Affiliates")

    # Add Services section
    add_services_section(with_section, channels)

    # Add ScheduleEntries section
    add_schedule_entries_section(with_section, schedule_data)

    # Add Lineups section
    lineups = ET.SubElement(with_section, "Lineups")
    if lineup_info.get("lineupId"):
        lineup = ET.SubElement(lineups, "Lineup", attrib={
            "id": safe_str(lineup_info["lineupId"]),
            "uid": f"!Lineup!{safe_str(lineup_info['lineupName'])}",
            "name": safe_str(lineup_info["lineupName"])
        })
        
        channels_element = ET.SubElement(lineup, "channels")
        for channel in channels:
            if channel.get("channelIndex"):
                ET.SubElement(channels_element, "Channel", attrib={
                    "uid": f"!Channel!{safe_str(lineup_info['lineupName'])}!{safe_str(channel['channelIndex'])}",
                    "lineup": safe_str(lineup_info["lineupId"]),
                    "service": f"s{safe_str(channel['channelIndex'])}",
                    "number": f"{safe_str(channel.get('majorChannel', ''))}." \
                             f"{safe_str(channel.get('minorChannel', ''))}"
                })

    # Convert to string and pretty-print
    raw_xml = ET.tostring(root, encoding="unicode", method="xml")
    pretty_xml = parseString(raw_xml).toprettyxml(indent="  ")

    return pretty_xml