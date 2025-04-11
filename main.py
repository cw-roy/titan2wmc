import os
import orjson
import requests
from dotenv import load_dotenv
from datetime import datetime
import pytz

# Load environment variables from .env file
load_dotenv()

# Get user credentials from environment
user_id = os.getenv("TITANTV_USER_ID")
login_name = os.getenv("TITANTV_USERNAME")
password = os.getenv("TITANTV_PASSWORD")

if not all([user_id, login_name, password]):
    raise ValueError("Missing one or more required environment variables: TITANTV_USER_ID, TITANTV_USERNAME, TITANTV_PASSWORD")

# API constants
lineup_id = "de9ee6e5-0d21-426b-87d7-be11545055d2"

# Define URLs
channels_url = f"https://titantv.com/api/channel/{user_id}/{lineup_id}"
lineup_url = f"https://titantv.com/api/lineup/{user_id}"
schedule_url = f"https://titantv.com/api/schedule/{user_id}/{lineup_id}/{{schedule_start}}/300"
user_url = f"https://titantv.com/api/user/{user_id}"

# Firefox user agent string
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'
}

# Define the output file path
data_folder = 'data'
os.makedirs(data_folder, exist_ok=True)
output_file = os.path.join(data_folder, 'api_output.json')

# Helper function to fetch and return JSON
def fetch_json(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch {url} (HTTP {response.status_code})")

# Fetch lineup data to get the time zone info
lineup_data = fetch_json(lineup_url)

# Get the local machine's current time and adjust for the local time zone
local_tz = pytz.timezone('America/Los_Angeles')  # Replace with your local time zone
local_time = datetime.now(local_tz)  # Get local time in specified time zone

# Format the schedule start time in the required format for the API
schedule_start = local_time.strftime("%Y%m%d%H%M")  # e.g., "202504081600"

# Construct the final schedule URL with dynamic schedule_start
schedule_url_dynamic = schedule_url.format(schedule_start=schedule_start)

# Fetch data from TitanTV API
channels_data = fetch_json(channels_url)
schedule_data = fetch_json(schedule_url_dynamic)

# Structure final output
combined_data = {
    'lineup': {
        'lineupId': lineup_data['lineups'][0]['lineupId'],
        'lineupName': lineup_data['lineups'][0]['lineupName'],
        'timezone': lineup_data['lineups'][0]['timeZone'],
        'utcOffset': lineup_data['lineups'][0]['utcOffset'],
        'observesDst': lineup_data['lineups'][0]['observesDst']
    },
    'channels': [],
    'schedule': []
}

# Process channels
for channel in channels_data.get('channels', []):
    combined_data['channels'].append({
        'channelId': channel['channelId'],
        'callSign': channel['callSign'],
        'network': channel['network'],
        'description': channel['description'],
        'hdCapable': channel['hdCapable'],
        'logo': channel['logo'],
        'sortOrder': channel['sortOrder'],
        'majorChannel': channel['majorChannel'],
        'minorChannel': channel['minorChannel']
    })

# Process schedule
for channel in schedule_data.get('channels', []):
    for day in channel.get('days', []):
        for event in day.get('events', []):
            combined_data['schedule'].append({
                'channelId': channel['channelIndex'],
                'eventId': event['eventId'],
                'startTime': event['startTime'],
                'endTime': event['endTime'],
                'title': event['title'],
                'description': event['description'],
                'programType': event['programType'],
                'tvRating': event.get('tvRating', ''),
                'showCard': event.get('showCard', '')
            })

# Write the output JSON
with open(output_file, 'wb') as f:
    f.write(orjson.dumps(combined_data, option=orjson.OPT_INDENT_2))

print(f"Fetched and combined TitanTV listing data saved to: {output_file}")


# import os
# import orjson
# import requests
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Get user credentials from environment
# user_id = os.getenv("TITANTV_USER_ID")
# login_name = os.getenv("TITANTV_USERNAME")
# password = os.getenv("TITANTV_PASSWORD")

# if not all([user_id, login_name, password]):
#     raise ValueError("Missing one or more required environment variables: TITANTV_USER_ID, TITANTV_USERNAME, TITANTV_PASSWORD")

# # API constants
# lineup_id = "de9ee6e5-0d21-426b-87d7-be11545055d2"
# schedule_start = "202504081600"  # Adjust this as needed
# schedule_duration = "300"        # In minutes

# # Define URLs
# channels_url = f"https://titantv.com/api/channel/{user_id}/{lineup_id}"
# lineup_url = f"https://titantv.com/api/lineup/{user_id}"
# schedule_url = f"https://titantv.com/api/schedule/{user_id}/{lineup_id}/{schedule_start}/{schedule_duration}"

# # Firefox user agent string
# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'
# }

# # Define the output file path
# data_folder = 'data'
# os.makedirs(data_folder, exist_ok=True)
# output_file = os.path.join(data_folder, 'api_output.json')

# # Helper function to fetch and return JSON
# def fetch_json(url):
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         raise Exception(f"Failed to fetch {url} (HTTP {response.status_code})")

# # Fetch data from TitanTV API
# lineup_data = fetch_json(lineup_url)
# channels_data = fetch_json(channels_url)
# schedule_data = fetch_json(schedule_url)

# # Structure final output (without user section)
# combined_data = {
#     'lineup': {
#         'lineupId': lineup_data['lineups'][0]['lineupId'],
#         'lineupName': lineup_data['lineups'][0]['lineupName'],
#         'timezone': lineup_data['lineups'][0]['timeZone'],
#         'utcOffset': lineup_data['lineups'][0]['utcOffset'],
#         'observesDst': lineup_data['lineups'][0]['observesDst']
#     },
#     'channels': [],
#     'schedule': []
# }

# # Process channels
# for channel in channels_data.get('channels', []):
#     combined_data['channels'].append({
#         'channelId': channel['channelId'],
#         'callSign': channel['callSign'],
#         'network': channel['network'],
#         'description': channel['description'],
#         'hdCapable': channel['hdCapable'],
#         'logo': channel['logo'],
#         'sortOrder': channel['sortOrder'],
#         'majorChannel': channel['majorChannel'],
#         'minorChannel': channel['minorChannel']
#     })

# # Process schedule
# for channel in schedule_data.get('channels', []):
#     for day in channel.get('days', []):
#         for event in day.get('events', []):
#             combined_data['schedule'].append({
#                 'channelId': channel['channelIndex'],
#                 'eventId': event['eventId'],
#                 'startTime': event['startTime'],
#                 'endTime': event['endTime'],
#                 'title': event['title'],
#                 'description': event['description'],
#                 'programType': event['programType'],
#                 'tvRating': event.get('tvRating', ''),
#                 'showCard': event.get('showCard', '')
#             })

# # Write the output JSON
# with open(output_file, 'wb') as f:
#     f.write(orjson.dumps(combined_data, option=orjson.OPT_INDENT_2))

# print(f"Fetched and combined TitanTV listing data saved to: {output_file}")
