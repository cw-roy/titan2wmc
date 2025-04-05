import os
import json
import logging

def ensure_data_directory():
    """Ensure the 'data' directory exists."""
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        logging.info(f"[+] Created directory: {data_dir}")
    return data_dir


def save_json_to_file(data, filename):
    """Save JSON data to a file in the 'data' directory."""
    data_dir = ensure_data_directory()
    filepath = os.path.join(data_dir, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        logging.info(f"[+] Saved JSON data to {filepath}")
    except Exception as e:
        logging.error(f"[-] Failed to save JSON to {filepath}: {e}")


def load_json(filename):
    """Load JSON data from a file in the 'data' directory."""
    data_dir = ensure_data_directory()
    filepath = os.path.join(data_dir, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        logging.info(f"[+] Loaded JSON data from {filepath}")
        return data
    except Exception as e:
        logging.error(f"[-] Failed to load JSON from {filepath}: {e}")
        return None