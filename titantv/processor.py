#!/usr/bin/env python3
# processor.py


def process_lineup_data(lineup_data):
    lineup = lineup_data["lineups"][0]
    return {
        "lineupId": lineup["lineupId"],
        "lineupName": lineup["lineupName"],
        "timezone": lineup["timeZone"],
        "utcOffset": lineup["utcOffset"],
        "observesDst": lineup["observesDst"],
    }


def process_channels_data(channels_data):
    return [
        {
            "channelId": c["channelId"],
            "callSign": c["callSign"],
            "network": c["network"],
            "description": c["description"],
            "hdCapable": c["hdCapable"],
            "logo": c["logo"],
            "sortOrder": c["sortOrder"],
            "majorChannel": c["majorChannel"],
            "minorChannel": c["minorChannel"],
        }
        for c in channels_data.get("channels", [])
    ]


def process_schedule_data(schedule_data):
    schedule = []
    for channel in schedule_data.get("channels", []):
        for day in channel.get("days", []):
            for event in day.get("events", []):
                schedule.append(
                    {
                        "channelId": channel["channelIndex"],
                        "eventId": event["eventId"],
                        "startTime": event["startTime"],
                        "endTime": event["endTime"],
                        "title": event["title"],
                        "description": event["description"],
                        "programType": event["programType"],
                        "tvRating": event.get("tvRating", ""),
                        "showCard": event.get("showCard", ""),
                    }
                )
    return schedule
