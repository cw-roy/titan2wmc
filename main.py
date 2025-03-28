import requests
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# TitanTV API Endpoints
LOGIN_URL = "https://titantv.com/api/login"
PROVIDERS_URL = "http://www.titantv.com/services/dataservice"  # Example URL for retrieving providers, needs to be adjusted based on actual API

# LOGIN_URL = "https://titantv.com/api/login"
# PROVIDERS_URL = "https://titantv.com/api/getProviders"  # Example URL for retrieving providers, needs to be adjusted based on actual API

# Retrieve credentials from environment variables
USERNAME = os.getenv("TITANTV_USERNAME")
PASSWORD = os.getenv("TITANTV_PASSWORD")

# Headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Referer": "https://titantv.com/",
    "Content-Type": "application/json"
}

# Start a session
session = requests.Session()

# Set up logging
logging.basicConfig(filename="titantv.log", level=logging.INFO, format='%(asctime)s - %(message)s')

def login():
    """Logs into TitanTV and prints out cookies and response content to help debug UUID."""
    if not USERNAME or not PASSWORD:
        print("[-] Missing credentials. Please set TITANTV_USERNAME and TITANTV_PASSWORD in the .env file.")
        logging.error("Missing credentials.")
        return None

    payload = {"loginName": USERNAME, "password": PASSWORD}

    response = session.post(LOGIN_URL, json=payload, headers=HEADERS)

    if response.status_code == 200 and "Set-Cookie" in response.headers:
        logging.info("[+] Login successful!")
        
        # Print all cookies to inspect them manually
        logging.info("[+] Cookies returned by the server:")
        for cookie in session.cookies:
            logging.info(f"Cookie name: {cookie.name}, value: {cookie.value}")
        
        # Optionally, print the response text for inspection
        logging.info("[+] Response text (for inspection):")
        logging.info(response.text)
        
        # Check if UUID is in the JSON response body (it's likely the userId field)
        try:
            data = response.json()  # Parse JSON response
            user_id = data.get("userId")
            
            if user_id:
                logging.info(f"[+] Found userId (UUID): {user_id}")
            else:
                logging.error("[-] userId (UUID) not found in the response body.")
        except ValueError:
            logging.error("[-] Response body is not JSON.")
        
        return session
    else:
        logging.error("[-] Login failed.")
        logging.error(f"Response: {response.text}")
        return None

def get_provider_ids():
    """Fetches the available provider IDs."""
    response = session.get(PROVIDERS_URL, headers=HEADERS)
    
    if response.status_code == 200:
        try:
            data = response.json()  # Assume the API returns a JSON list of providers
            provider_ids = [provider['ProviderId'] for provider in data.get("providers", [])]
            logging.info(f"[+] Found Provider IDs: {provider_ids}")
            return provider_ids
        except ValueError:
            logging.error("[-] Failed to parse provider data from response.")
    else:
        logging.error(f"[-] Failed to fetch provider data. Status code: {response.status_code}")
        return []

# Test login, fetch provider IDs, and log results
if __name__ == "__main__":
    session = login()
    if session:
        logging.info("[+] Ready to proceed with provider ID retrieval.")
        provider_ids = get_provider_ids()
        if provider_ids:
            logging.info(f"[+] Retrieved Provider IDs: {provider_ids}")
        else:
            logging.warning("[-] No Provider IDs found.")





# import requests
# from dotenv import load_dotenv
# import os

# # Load environment variables from .env file
# load_dotenv()

# # TitanTV API Endpoints
# LOGIN_URL = "https://titantv.com/api/login"

# # Retrieve credentials from environment variables
# USERNAME = os.getenv("TITANTV_USERNAME")
# PASSWORD = os.getenv("TITANTV_PASSWORD")

# # Headers to mimic a real browser
# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
#     "Referer": "https://titantv.com/",
#     "Content-Type": "application/json"
# }

# # Start a session
# session = requests.Session()

# def login():
#     """Logs into TitanTV and returns the session."""
#     if not USERNAME or not PASSWORD:
#         print("[-] Missing credentials. Please set TITANTV_USERNAME and TITANTV_PASSWORD in the .env file.")
#         return None

#     payload = {"loginName": USERNAME, "password": PASSWORD}

#     response = session.post(LOGIN_URL, json=payload, headers=HEADERS)

#     if response.status_code == 200 and "Set-Cookie" in response.headers:
#         print("[+] Login successful!")
#         return session  # Session retains authentication cookies
#     else:
#         print("[-] Login failed.")
#         print("Response:", response.text)
#         return None

# # Test login
# if __name__ == "__main__":
#     session = login()
#     if session:
#         print("[+] Ready to fetch TV listings!")
