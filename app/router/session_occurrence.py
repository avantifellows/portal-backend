from fastapi import APIRouter, HTTPException, Request
from typing import Union
import requests
from settings import settings
from datetime import datetime
from models import SessionOpenResponse, SessionCloseResponse

router = APIRouter(prefix="/session-occurrence", tags=["Session Occurrence"])
session_db_url = settings.db_url + "/session/"
session_occurrence_db_url = settings.db_url + "/session-occurrence/"
session_start_buffer_time = 900000


def get_current_timestamp():
    """
    Returns current timestamp
    """
    return datetime.today().timestamp()


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
    session_timestamp = get_timestamp(parsed_time)
    current_timestamp = get_current_timestamp()

    return (session_timestamp, current_timestamp)


def has_session_started(start_time: str):
    """
    Checks if session has started
    - If session time is given and session start date is less than or equal to current date, returns True
    - Otherwise, returns False
    """
    if start_time is not None:
        session_start_timestamp, current_timestamp = build_datetime_and_timestamp(
            start_time
        )
        return session_start_timestamp <= current_timestamp + session_start_buffer_time
    return True


def has_session_ended(end_time: str):
    """
    Checks if session has ended
    - If end time is given and if session end date is greater than or equal to current date, returns True
    - Else, always returns True
    """
    if end_time is not None:
        session_end_timestamp, current_timestamp = build_datetime_and_timestamp(
            end_time
        )
        return session_end_timestamp <= current_timestamp + session_start_buffer_time
    return True


@router.get("/", response_model=Union[SessionOpenResponse, SessionCloseResponse])
async def get_session_occurrence_data(request: Request):
    """
    This API returns session occurrence details corresponding to the provided session ID, if the ID exists in the database and if the session is open

    Parameters:
    session_id (str): The ID against which details need to be retrieved

    Returns:
    list: Returns session occurrence details if the session ID exists in the database and the session is open, false if the session is closed. If the ID does not exist, 404 is returned

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
        if key not in ["name", "session_id"]:
            return HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(session_occurrence_db_url, params=query_params)

    if response.status_code == 200:
        if len(response.json()) != 0:

            session_occurrence_data = response.json()[0]
            response = requests.get(session_db_url, params=query_params)

            if response.status_code == 200:
                session_data = response.json()[0]
                if (
                    session_data["is_active"]
                    and has_session_started(session_occurrence_data["start_time"])
                    and has_session_ended(session_occurrence_data["end_time"])
                ):
                    session_data["is_session_open"] = True
                    return session_data
                return {"is_session_open": False}
            raise HTTPException(
                status_code=response.status_code, detail=response.errors
            )

        return HTTPException(status_code=404, detail="Session ID does not exist!")
    raise HTTPException(status_code=response.status_code, detail=response.errors)
