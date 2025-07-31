from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from models import SessionResponse
from helpers import db_request_token
from logger_config import get_logger

router = APIRouter(prefix="/session-occurrence", tags=["Session Occurrence"])
session_db_url = settings.db_url + "/session/"
session_occurrence_db_url = settings.db_url + "/session-occurrence/"
logger = get_logger()


@router.get("/", response_model=SessionResponse)
async def get_session_occurrence_data(request: Request):
    """
    This API returns session occurrence details corresponding to the provided session ID, if the ID exists in the database and if the session is open

    Parameters:
    session_id (str): The ID against which details need to be retrieved

    Returns:
    list: Returns session occurrence details if the session ID exists in the database and the session is open, false if the session is closed. If the ID does not exist, 404 is returned
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

    # First check if session exists at all
    try:
        session_params = {"session_id": session_id}
        session_response = requests.get(
            session_db_url,
            params=session_params,
            headers=db_request_token(),
            timeout=60,
        )
    except Exception as e:
        logger.error(f"Failed to connect to session API: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to connect to session service"
        )

    if session_response.status_code != 200:
        logger.error(
            f"Session API returned status {session_response.status_code} for session_id: {session_id}"
        )
        raise HTTPException(status_code=404, detail="Session ID does not exist!")

    session_data_list = session_response.json()
    if not isinstance(session_data_list, list) or len(session_data_list) == 0:
        logger.error(f"No session data found for session_id: {session_id}")
        raise HTTPException(status_code=404, detail="Session ID does not exist!")

    session_data = session_data_list[0]
    logger.info(f"Retrieved session data for session {session_id}")

    # Check if this is a quiz session to determine query strategy
    is_quiz_session = session_data.get("platform") == "quiz" or (
        session_data.get("purpose", {}).get("sub-type") == "quiz"
    )

    # For quiz sessions, query for occurrences that encompass current time
    # For live class sessions, query for today's occurrences (existing behavior)
    if is_quiz_session:
        logger.info(
            f"Detected quiz session {session_id}, querying for active occurrences"
        )
        query_params["is_start_time"] = (
            "active"  # Query for currently active occurrences
        )
    else:
        logger.info(
            f"Detected live class session {session_id}, querying for today's occurrences"
        )
        query_params["is_start_time"] = "today"

    try:
        response = requests.get(
            session_occurrence_db_url,
            params=query_params,
            headers=db_request_token(),
            timeout=60,
        )
    except Exception as e:
        logger.error(f"Failed to connect to session occurrence API: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to connect to session occurrence service"
        )

    if response.status_code == 200:
        try:
            session_occurrences = response.json()
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database returned invalid JSON at position {e.pos}",
            )

        if not isinstance(session_occurrences, list):
            logger.error(
                f"Unexpected response format from session occurrence API: {type(session_occurrences)}"
            )
            raise HTTPException(
                status_code=500,
                detail="Invalid response format from session occurrence service",
            )

        # Session exists - check if there are active occurrences
        if len(session_occurrences) > 0:
            logger.info(
                f"Found {len(session_occurrences)} session occurrences for session {session_id}"
            )
            # Session has active occurrences - check if session is enabled
            session_data["is_session_open"] = bool(session_data.get("is_active", False))
            if session_data["is_session_open"]:
                session_data["session_occurrence_id"] = session_occurrences[0].get("id")
                logger.info(f"Session {session_id} is currently open")
            else:
                logger.info(f"Session {session_id} exists but is currently closed")
        else:
            if is_quiz_session:
                logger.info(
                    f"Quiz session {session_id} exists but no active occurrences found"
                )
            else:
                logger.info(
                    f"Live class session {session_id} exists but no occurrences found for today"
                )
            # Session exists but no active occurrences - "no class/quiz right now"
            session_data["is_session_open"] = False

        return session_data

    logger.error(
        f"Session occurrence API returned status {response.status_code} for session_id: {session_id}"
    )
    raise HTTPException(status_code=404, detail="Session ID not found!")
