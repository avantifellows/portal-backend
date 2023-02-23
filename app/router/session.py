from fastapi import APIRouter, HTTPException
import requests
from settings import settings
from datetime import datetime
from models import SessionResponse

router = APIRouter(prefix="/session", tags=["Session"])
session_db_url = settings.db_url + "/session/"
session_start_buffer_time = 900000


def get_current_date():
    """
    Returns current date
    """
    return datetime.today().date()


def get_current_timestamp():
    """
    Returns current timestamp
    """
    return datetime.today().timestamp()


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


def build_datetime_and_timestamp(date_time: str):
    """
    Parses the given datetime into separate strings of date and timstamp
    """
    parsed_time = datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%SZ")
    session_date, session_timestamp = get_date(parsed_time), get_timestamp(parsed_time)
    current_date, current_timestamp = get_current_date(), get_current_timestamp()
    repeated_session_datetime = datetime(
        current_date.year,
        current_date.month,
        current_date.day,
        parsed_time.hour,
        parsed_time.minute,
        parsed_time.second,
    )
    return (
        session_date,
        session_timestamp,
        current_date,
        current_timestamp,
        repeated_session_datetime,
    )


def has_session_started(start_time: str, repeat_schedule: str):
    """
    Checks if session has started
    - If session start date is less than or equal to current date:
        - If session is not repeating, checks if the session start timestamp is less than the current timestamp
        - If session is repeating, builds a timestamp using current date and session start time and checks that with the current timestamp
    - Otherwise, returns False
    """
    if start_time is not None:
        (
            session_start_date,
            session_start_timestamp,
            current_date,
            current_timestamp,
            repeated_session_start_datetime,
        ) = build_datetime_and_timestamp(start_time)
        if session_start_date <= current_date:
            if repeat_schedule is None:
                return (
                    session_start_timestamp
                    <= current_timestamp + session_start_buffer_time
                )
            else:
                return (
                    repeated_session_start_datetime
                    <= current_timestamp + session_start_buffer_time
                )
        return False
    return True


def has_session_ended(end_time: str, repeat_schedule: str):
    """
    Checks if session has ended
    - If end time is given:
        - If session end date is greater than or equal to current date:
            - If session is not repeating, checks if the current timestamp is less than or equal to session end timestamp
            - If session is repeating, builds a timestamp using current date and session end time and checks that with current timestamp
    - Else, always returns True
    """
    if end_time is not None:
        (
            session_end_date,
            session_end_timestamp,
            current_date,
            current_timestamp,
            repeated_session_end_datetime,
        ) = build_datetime_and_timestamp(end_time)
        if session_end_date >= current_date:
            if repeat_schedule is not None:
                return current_timestamp <= repeated_session_end_datetime
            return current_timestamp <= session_end_timestamp
        return False
    return True


def is_session_repeating(repeat_schedule: str):
    """
    Checks if the repeating schedule matches to the current day.
    """
    if repeat_schedule is not None:
        if repeat_schedule["type"] == "weekly":
            return datetime.today().weekday() in repeat_schedule["params"]
    return True


@router.get("/", response_model=SessionResponse)
async def get_session_data(request: Request):
    """
    This API returns session details corresponding to the provided session ID, if the ID exists in the database and if the session is open

    Parameters:
    session_id (str): The ID against which details need to be retrieved

    Returns:
    list: Returns session details if the session ID exists in the database and the session is open, false if the session is closed. If the ID does not exist, 404 is returned

    Example:
    > $BASE_URL/session/1234
    returns [{session_data}]

    > $BASE_URL/session/{closed_session_id}
    returns false

    > $BASE_URL/session/{invalid_id}
    returns {
        "status_code": 404,
        "detail": "Session ID does not exist!",
        "headers": null
    }
    """
    query_params = {}
    for key in request.query_params.keys():
        if key not in ['name','session_id']:
            return HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(session_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) != 0:
            session_data = response.json()[0]
            if (
                session_data["is_active"]
                and has_session_started(
                    session_data["start_time"], session_data["repeat_schedule"]
                )
                and has_session_ended(
                    session_data["end_time"], session_data["repeat_schedule"]
                )
                and is_session_repeating(session_data["repeat_schedule"])
            ):
                return session_data
            return False
        return HTTPException(status_code=404, detail="Session ID does not exist!")
    raise HTTPException(status_code=response.status_code, detail=response.errors)
