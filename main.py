from datetime import datetime
import logging
from api_requests import (
    login,
    validate_user,
    # validate_lineup,
    fetch_provider_info,
    fetch_lineup_info,
    fetch_channel_info,
    fetch_schedule,
)

# Set up logging
logging.basicConfig(filename="titantv.log", level=logging.INFO, format='%(asctime)s - %(message)s')

DEFAULT_DURATION = "300"

def get_current_start_time():
    """Generate start time based on the current date and time."""
    now = datetime.now()  # Get current date and time
    start_time = now.strftime("%Y%m%d%H%M")  # Format the date as 'YYYYMMDDHHMM'
    return start_time

if __name__ == "__main__":
    try:
        logging.info("[+] Start run...")
        session = login()
        if session:
            logging.info("[+] Ready to proceed with user and provider validation.")
            
            # Validate user
            if validate_user():
                # Fetch provider information
                provider_info = fetch_provider_info()
                if not provider_info:
                    logging.error("[-] Failed to fetch provider information. Exiting.")
                    exit(1)
                
                # Fetch lineup information
                lineup_info = fetch_lineup_info()
                if not lineup_info:
                    logging.error("[-] Failed to fetch lineup information. Exiting.")
                    exit(1)
                
                # Fetch channel information
                channels = fetch_channel_info(lineup_info['lineupId'])
                if not channels:
                    logging.error("[-] Failed to fetch channel information. Exiting.")
                    exit(1)

                # Fetch schedule
                lineup_id = lineup_info.get("lineupId")
                start_time = get_current_start_time()
                duration = DEFAULT_DURATION
                schedule_data = fetch_schedule(lineup_id, start_time, duration)
                if schedule_data:
                    logging.info("[+] Schedule fetched successfully.")
                else:
                    logging.error("[-] Failed to fetch schedule.")
            else:
                logging.error("[-] User validation failed.")
        logging.info("[+] End of run.")
    finally:
        if session:
            session.close()
            logging.info("[+] Session closed.")
