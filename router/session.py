from fastapi import APIRouter
import requests
from settings import settings
from datetime import datetime

router = APIRouter(prefix="/session", tags=["Session"])

def get_current_datetime():
    return datetime.today()

def get_current_date():
    return datetime.today().date()

def get_current_timestamp():
    return datetime.today().timestamp()

def get_date(datetime: datetime):
    return datetime.date()

def get_timestamp(datetime: datetime):
    return datetime.timestamp()

def is_start_time_valid(start_time: str, repeat_schedule: str):
    parsed_start_time = datetime.strptime(start_time,'%Y-%m-%dT%H:%M:%SZ')
    session_start_date, session_start_timestamp = get_date(parsed_start_time), get_timestamp(parsed_start_time)
    current_date, current_timestamp = get_current_date(), get_current_timestamp()
    repeated_session_start = datetime(current_date.year, current_date.month, current_date.day, parsed_start_time.hour, parsed_start_time.minute, parsed_start_time.second)
    if session_start_date <= current_date:
        if repeat_schedule is None:
            return session_start_timestamp <= current_timestamp + 900000
        else:
            return repeated_session_start <= current_timestamp + 900000
    return False

def is_end_time_valid(end_time: str, repeat_schedule: str):
    if end_time is not None:
        parsed_end_time = datetime.strptime(end_time,'%Y-%m-%dT%H:%M:%SZ')
        session_end_date, session_end_timestamp = get_date(parsed_end_time), get_timestamp(parsed_end_time)
        current_date, current_timestamp = get_current_date(), get_current_timestamp()
        if session_end_date >= current_date:
            if repeat_schedule is not None:
                return current_timestamp <= datetime(current_date.year, current_date.month, current_date.day, parsed_end_time.hour, parsed_end_time.minute, parsed_end_time.second)
            return current_timestamp <= session_end_timestamp
        return False
    return True


def is_repeat_schedule_valid(repeat_schedule: str):
    if repeat_schedule is not None:
        if repeat_schedule["type"] == "weekly":
            return get_current_datetime().weekday() in repeat_schedule["params"]
    return True

@router.post("/get-session-data")
def get_session_data(session_id: str):
    r = requests.get(settings.db_url + "session/" + session_id)
    session_data = r.json()
    if "errors" not in session_data:
        if session_data["is_active"] and is_start_time_valid(session_data["start_time"], session_data["repeat_schedule"]) and is_end_time_valid(session_data["end_time"], session_data["repeat_schedule"]) and is_repeat_schedule_valid(session_data["repeat_schedule"]):
            return session_data
    return False