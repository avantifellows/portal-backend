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
        raise HTTPException(status_code=400, detail="session_id parameter is required!")

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
        raise HTTPException(status_code=404, detail="Session ID does not exist!")

    session_data_list = session_response.json()
    if not isinstance(session_data_list, list) or len(session_data_list) == 0:
        raise HTTPException(status_code=404, detail="Session ID does not exist!")

    session_data = session_data_list[0]

    # Now check for today's occurrences
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
            raise HTTPException(
                status_code=500,
                detail="Invalid response format from session occurrence service",
            )

        # Session exists - check if there are occurrences today
        if len(session_occurrences) > 0:
            # Session has occurrences today - check if active
            session_data["is_session_open"] = bool(session_data.get("is_active", False))
            if session_data["is_session_open"]:
                session_data["session_occurrence_id"] = session_occurrences[0].get("id")
        else:
            # Session exists but no occurrences today - "no class right now"
            session_data["is_session_open"] = False

        return session_data

    raise HTTPException(status_code=404, detail="Session ID not found!")
