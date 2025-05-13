#!/usr/bin/env python3
# mxf_generator.py

import logging
import os

from lxml import etree


def generate_mxf(data, output_path):
    logging.info("Generating MXF file...")
    mxf = etree.Element("MXF", xmlns="http://www.microsoft.com")

    # Lineups
    lineup_elem = etree.SubElement(mxf, "Lineups")
    lineup = data["lineup"]
    lineup_node = etree.SubElement(
        lineup_elem, "Lineup", id="1", uid=lineup["lineupId"]
    )  # noqa: E501
    etree.SubElement(lineup_node, "Name").text = lineup["lineupName"]
    etree.SubElement(lineup_node, "TimeZone").text = lineup["timezone"]
    etree.SubElement(lineup_node, "UTCOffset").text = str(lineup["utcOffset"])
    etree.SubElement(lineup_node, "ObservesDaylightSaving").text = str(
        lineup["observesDst"]
    ).lower()  # noqa: E501

    # Channels
    channels_elem = etree.SubElement(mxf, "Channels")
    for ch in data["channels"]:
        ch_elem = etree.SubElement(channels_elem, "Channel", id=str(ch["channelId"]))
        etree.SubElement(ch_elem, "CallSign").text = ch["callSign"]
        etree.SubElement(ch_elem, "Name").text = ch["network"]
        etree.SubElement(ch_elem, "Description").text = ch["description"]
        etree.SubElement(ch_elem, "HD").text = str(ch["hdCapable"]).lower()
        etree.SubElement(ch_elem, "Logo").text = ch["logo"]
        etree.SubElement(ch_elem, "MajorChannel").text = str(ch["majorChannel"])
        etree.SubElement(ch_elem, "MinorChannel").text = str(ch["minorChannel"])
        etree.SubElement(ch_elem, "Lineup").text = "1"

    # Programs
    programs_elem = etree.SubElement(mxf, "Programs")
    for prog in data["schedule"]:
        prog_elem = etree.SubElement(programs_elem, "Program", id=str(prog["eventId"]))
        etree.SubElement(prog_elem, "Title").text = prog["title"]
        etree.SubElement(prog_elem, "Description").text = prog["description"]
        etree.SubElement(prog_elem, "StartTime").text = prog["startTime"]
        etree.SubElement(prog_elem, "EndTime").text = prog["endTime"]
        etree.SubElement(prog_elem, "ProgramType").text = prog["programType"]
        etree.SubElement(prog_elem, "TVRating").text = prog.get("tvRating", "")
        etree.SubElement(prog_elem, "ShowCard").text = prog.get("showCard", "")
        etree.SubElement(prog_elem, "Channel").text = str(prog["channelId"])

    # ScheduleEntries
    schedule_elem = etree.SubElement(mxf, "ScheduleEntries")
    for prog in data["schedule"]:
        entry = etree.SubElement(schedule_elem, "ScheduleEntry")
        etree.SubElement(entry, "Channel").text = str(prog["channelId"])
        etree.SubElement(entry, "Program").text = str(prog["eventId"])
        etree.SubElement(entry, "StartTime").text = prog["startTime"]
        etree.SubElement(entry, "EndTime").text = prog["endTime"]

    # Ensure the output path is platform-agnostic
    output_file_path = os.path.join(output_path)  # Ensure output path compatibility

    tree = etree.ElementTree(mxf)
    tree.write(
        output_file_path, pretty_print=True, xml_declaration=True, encoding="utf-8"
    )  # noqa: E501
    logging.info(f"MXF file written to {output_file_path}")
