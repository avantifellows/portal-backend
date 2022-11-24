from fastapi import APIRouter
import requests
from settings import settings
from datetime import datetime

router = APIRouter(prefix="/session", tags=["Session"])
session_db_url = settings.db_url + "session/"
session_start_buffer_time = 900000

def get_current_datetime():
    """
    Returns current datetime
    """
    return datetime.today()

def get_current_date():
    """
    Returns current date
    """
    return get_current_datetime.date()

def get_current_timestamp():
    """
    Returns current timestamp
    """
    return get_current_datetime.timestamp()

def get_date(datetime: datetime):
    """
    Returns date for the given datetime
    """
    return datetime.date()

def get_timestamp(datetime: datetime):
    """
    Returns timestamp for the given datetime
    """
    return datetime.timestamp()

def is_start_time_valid(start_time: str, repeat_schedule: str):
    """
    Checks if session start time is valid
    - If session start date is less than or equal to current date:
        - If session is not repeating, checks if the session start timestamp is less than the current timestamp
        - If session is repeating, builds a timestamp using current date and session start time and checks that with the current timestamp
    - Otherwise, returns False
    """
    parsed_start_time = datetime.strptime(start_time,'%Y-%m-%dT%H:%M:%SZ')
    session_start_date, session_start_timestamp = get_date(parsed_start_time), get_timestamp(parsed_start_time)
    current_date, current_timestamp = get_current_date(), get_current_timestamp()
    repeated_session_start_datetime = datetime(current_date.year, current_date.month, current_date.day, parsed_start_time.hour, parsed_start_time.minute, parsed_start_time.second)
    if session_start_date <= current_date:
        if repeat_schedule is None:
            return session_start_timestamp <= current_timestamp + session_start_buffer_time
        else:
            return repeated_session_start_datetime <= current_timestamp + session_start_buffer_time
    return False

def is_end_time_valid(end_time: str, repeat_schedule: str):
    """
    Checks if session end time is valid
    - If end time is given:
        - If session end date is greater than or equal to current date:
            - If session is not repeating, checks if the current timestamp is less than or equal to session end timestamp
            - If session is repeating, builds a timestamp using current date and session end time and checks that with current timestamp
    - Else, always returns True
    """
    if end_time is not None:
        parsed_end_time = datetime.strptime(end_time,'%Y-%m-%dT%H:%M:%SZ')
        session_end_date, session_end_timestamp = get_date(parsed_end_time), get_timestamp(parsed_end_time)
        current_date, current_timestamp = get_current_date(), get_current_timestamp()
        repeated_session_end_datetime = datetime(current_date.year, current_date.month, current_date.day, parsed_end_time.hour, parsed_end_time.minute, parsed_end_time.second)
        if session_end_date >= current_date:
            if repeat_schedule is not None:
                return current_timestamp <= repeated_session_end_datetime
            return current_timestamp <= session_end_timestamp
        return False
    return True


def is_repeat_schedule_valid(repeat_schedule: str):
    """
    Checks if the repeating schedule matches to the current day.
    """
    if repeat_schedule is not None:
        if repeat_schedule["type"] == "weekly":
            return get_current_datetime().weekday() in repeat_schedule["params"]
    return True

@router.post("/get-session-data")
def get_session_data(session_id: str):
    """
    API to get details about a session if the session is active.
    Otherwise, returns False to denote session is not active.
    """
    session_data = requests.get(session_db_url + session_id).json()
    if "errors" not in session_data:
        if session_data["is_active"] and is_start_time_valid(session_data["start_time"], session_data["repeat_schedule"]) and is_end_time_valid(session_data["end_time"], session_data["repeat_schedule"]) and is_repeat_schedule_valid(session_data["repeat_schedule"]):
            return session_data
        return False
    return False