import requests
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# TitanTV API Endpoints
LOGIN_URL = "https://titantv.com/api/login"
LINEUP_URL = "https://titantv.com/api/lineup/881"  # Replace '881' with the actual provider ID you're using

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
        return session
    else:
        logging.error("[-] Login failed.")
        logging.error(f"Response: {response.text}")
        return None

def validate_provider_id():
    """Validates provider ID 881."""
    logging.info("[+] Validating provider ID...")

    # Use the provider ID directly in the URL for the lineup
    response = session.get(LINEUP_URL, headers=HEADERS)

    if response.status_code == 200:
        logging.info("[+] Provider ID and UUID validated successfully.")
    else:
        logging.error(f"[-] Failed to validate provider ID. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")

# Test login and provider validation, log success or failure
if __name__ == "__main__":
    session = login()
    if session:
        logging.info("[+] Ready to proceed with provider ID validation.")
        validate_provider_id()