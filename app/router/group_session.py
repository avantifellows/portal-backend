from fastapi import APIRouter
import requests
from app.routes import group_session_db_url
from app.helpers import db_request_token, is_response_valid, is_response_empty


router = APIRouter(prefix="/session-group", tags=["Session-Group"])


@router.get("/{session_id}")
def get_group_for_session(session_id: str):
    response = requests.get(
        group_session_db_url + "/session-auth-group",
        params={"session_id": session_id},
        headers=db_request_token(),
    )
    if is_response_valid(response, "Group Session API could not fetch the data!"):
        auth_group_data = is_response_empty(
            response.json(), True, "Auth group data does not exist!"
        )
        if auth_group_data:
            return auth_group_data
