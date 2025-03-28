import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# TitanTV API Endpoints
LOGIN_URL = "https://titantv.com/api/login"

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

def login():
    """Logs into TitanTV and returns the session."""
    if not USERNAME or not PASSWORD:
        print("[-] Missing credentials. Please set TITANTV_USERNAME and TITANTV_PASSWORD in the .env file.")
        return None

    payload = {"loginName": USERNAME, "password": PASSWORD}

    response = session.post(LOGIN_URL, json=payload, headers=HEADERS)

    if response.status_code == 200 and "Set-Cookie" in response.headers:
        print("[+] Login successful!")
        return session  # Session retains authentication cookies
    else:
        print("[-] Login failed.")
        print("Response:", response.text)
        return None

# Test login
if __name__ == "__main__":
    session = login()
    if session:
        print("[+] Ready to fetch TV listings!")
