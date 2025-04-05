import logging
import requests

def login(session, username, password, headers):
    """Logs into TitanTV and prints out cookies and response content to help debug UUID."""
    if not username or not password:
        logging.error("[-] Missing credentials. Please set TITANTV_USERNAME and TITANTV_PASSWORD in the .env file.")
        return None

    payload = {"loginName": username, "password": password}
    login_url = "https://titantv.com/api/login"
    response = session.post(login_url, json=payload, headers=headers)

    if response.status_code == 200 and "Set-Cookie" in response.headers:
        logging.info("[+] Login successful!")
        return session
    else:
        logging.error("[-] Login failed.")
        logging.error(f"Response: {response.text}")
        return None


def validate_user(session, user_url, headers):
    """Fetches user data to validate user ID and lineup."""
    logging.info("[+] Validating user ID...")
    response = session.get(user_url, headers=headers)

    if response.status_code == 200:
        logging.info("[+] User validated successfully.")
        return True
    else:
        logging.error(f"[-] Failed to validate user ID. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return False


def validate_lineup(session, lineup_url, headers):
    """Fetches lineup data to validate lineup ID."""
    logging.info("[+] Validating provider lineup...")
    response = session.get(lineup_url, headers=headers)

    if response.status_code == 200:
        logging.info("[+] Provider lineup validated successfully.")
        return True
    else:
        logging.error(f"[-] Failed to validate lineup. Status code: {response.status_code}")
        logging.error(f"[-] Response content: {response.text}")
        return False