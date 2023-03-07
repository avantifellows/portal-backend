from fastapi import APIRouter, HTTPException
import requests
from settings import settings

router = APIRouter(prefix="/session-group", tags=["Session-Group"])
session_group_db_url = settings.db_url + "/group-session/"


@router.get("/{session_id}")
def get_group_for_session(session_id: str):
    """
    This API returns group ID corresponding to the provided session ID, if the ID exists in the database

    Parameters:
    session_id (str): The ID against which group ID needs to be retrieved

    Returns:
    list: Returns group ID if the session ID exists in the database. If the ID does not exist, 404 is returned

    Example:
    > $BASE_URL/session/1234
    returns [{group_id: 123}]

    > $BASE_URL/session/{invalid_id}
    returns {
        "status_code": 404,
        "detail": "Session ID does not exist!",
        "headers": null
    }
    """
    response = requests.get(session_group_db_url + session_id)
    if response.status_code == 200:
        if len(response.json()) != 0:
            return response.json()
        return HTTPException(status_code=404, detail="Session does not exist!")
    return HTTPException(status_code=response.status_code, detail=response.errors)
