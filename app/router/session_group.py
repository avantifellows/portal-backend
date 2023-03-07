from fastapi import APIRouter, HTTPException
import requests
from settings import settings

router = APIRouter(prefix="/session-group", tags=["Session-Group"])
session_group_db_url = settings.db_url + "/group-session/"


@router.get("/{session_id}")
def get_group_for_session(session_id: str):
    response = requests.get(session_group_db_url + session_id)
    if response.status_code == 200:
        if len(response.json()) != 0:
            return response.json()
        return HTTPException(status_code=404, detail="Session does not exist!")
    return HTTPException(status_code=response.status_code, detail=response.errors)
