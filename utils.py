from datetime import datetime

def get_current_start_time():
    """Generate start time based on the current date and time."""
    now = datetime.now()  # Get current date and time
    start_time = now.strftime("%Y%m%d%H%M")  # Format the date as 'YYYYMMDDHHMM'
    return start_time