from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from datetime import datetime
from models import SessionResponse
import pytz
from helpers import db_request_token
from logger_config import get_logger

IST = pytz.timezone("Asia/Kolkata")
router = APIRouter(prefix="/session-occurrence", tags=["Session Occurrence"])
session_db_url = settings.db_url + "/session/"
session_occurrence_db_url = settings.db_url + "/session-occurrence/"
logger = get_logger()


def build_date_and_time(date_time: str):
    """
    Parses string into date and time strings
    """
    parsed_time = datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%SZ")
    date_string, time_string = str(parsed_time).split()
    return (date_string, time_string)


def get_current_datetime():
    """
    Returns current datetime
    """
    current_datetime = datetime.now(IST)

    return build_date_and_time(current_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"))


def has_session_started(start_time: str):
    """
    Checks if session has started
    - If session time is given and session start date is less than or equal to current date, returns True
    - Otherwise, returns False
    """
    if start_time is not None:
        session_start_date, session_start_time = build_date_and_time(start_time)
        current_date, current_time = get_current_datetime()
        return session_start_date == current_date and session_start_time <= current_time
    return True


def has_session_not_ended(end_time: str):
    """
    Checks if session has not ended
    - If end time is given and if session end date is greater than or equal to current date, returns True
    - Else, always returns True
    """
    if end_time is not None:
        session_end_date, session_end_time = build_date_and_time(end_time)
        current_date, current_time = get_current_datetime()

        return session_end_date == current_date and session_end_time >= current_time
    return True


@router.get("/", response_model=SessionResponse)
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
    returns {"is_session_open": False}

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
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    session_id = query_params.get("session_id")
    if not session_id:
        logger.error("No session_id provided in query parameters")
        raise HTTPException(status_code=400, detail="session_id parameter is required!")

    logger.info("Searching for session {} ...".format(session_id))

    try:
        response = requests.get(
            session_occurrence_db_url, params=query_params, headers=db_request_token()
        )
    except Exception as e:
        logger.error(f"Failed to connect to session occurrence API: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to connect to session occurrence service"
        )

    if response.status_code == 200:
        session_occurrences = response.json()

        if not isinstance(session_occurrences, list):
            logger.error(
                f"Unexpected response format from session occurrence API: {type(session_occurrences)}"
            )
            raise HTTPException(
                status_code=500,
                detail="Invalid response format from session occurrence service",
            )

        if len(session_occurrences) != 0:
            logger.info(
                f"Found {len(session_occurrences)} session occurrences for session {session_id}"
            )

            # session exists because occurrences exist
            # fetch session data
            try:
                session_response = requests.get(
                    session_db_url, params=query_params, headers=db_request_token()
                )
            except Exception as e:
                logger.error(f"Failed to connect to session API: {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Failed to connect to session service"
                )

            if session_response.status_code == 200:
                session_data_list = session_response.json()

                if (
                    not isinstance(session_data_list, list)
                    or len(session_data_list) == 0
                ):
                    logger.error(f"No session data found for session_id: {session_id}")
                    raise HTTPException(
                        status_code=404, detail="Session ID does not exist!"
                    )

                session_data = session_data_list[0]
                logger.info(f"Retrieved session data for session {session_id}")
            else:
                logger.error(
                    f"Session API returned status {session_response.status_code} for session_id: {session_id}"
                )
                raise HTTPException(
                    status_code=404, detail="Session ID does not exist!"
                )

            session_data["is_session_open"] = False
            if session_data.get("is_active", False):
                for session_occurrence in session_occurrences:
                    if has_session_started(
                        session_occurrence.get("start_time")
                    ) and has_session_not_ended(session_occurrence.get("end_time")):
                        session_data["is_session_open"] = True
                        session_data["session_occurrence_id"] = session_occurrence.get(
                            "id"
                        )
                        logger.info(f"Session {session_id} is currently open")
                        break  # matched a session occurrence

                if not session_data["is_session_open"]:
                    logger.info(f"Session {session_id} exists but is currently closed")

            return session_data

        logger.warning(f"No session occurrences found for session_id: {session_id}")
        raise HTTPException(status_code=404, detail="Session ID does not exist!")

    logger.error(
        f"Session occurrence API returned status {response.status_code} for session_id: {session_id}"
    )
    raise HTTPException(status_code=404, detail="Session ID not found!")
