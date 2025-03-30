import logging
from api_requests import (
    login,
    validate_user,
    fetch_provider_info,
    fetch_lineup_info,
    fetch_channel_info,
    fetch_schedule,
)
from data_processing import extract_listings, summarize_listings, save_listings_to_file
from utils import get_current_start_time  # Import the utility function

# Set up logging
logging.basicConfig(filename="titantv.log", level=logging.INFO, format='%(asctime)s - %(message)s')

DEFAULT_DURATION = "300"

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
                    
                    # Process and save listings
                    listings = extract_listings(schedule_data)
                    summarize_listings(listings)
                    save_listings_to_file(listings)
                else:
                    logging.error("[-] Failed to fetch schedule.")
            else:
                logging.error("[-] User validation failed.")
        logging.info("[+] End of run.")
    finally:
        if session:
            session.close()
            logging.info("[+] Session closed.")
