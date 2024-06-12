from fastapi import APIRouter, HTTPException
import requests
from settings import settings
from routes import group_session_db_url, group_db_url, auth_group_db_url
from helpers import db_request_token, is_response_valid, is_response_empty


router = APIRouter(prefix="/session-group", tags=["Session-Group"])


def get_auth_group_details(auth_group_id):
    auth_group_response = requests.get(
        auth_group_db_url, params={"id": auth_group_id}, headers=db_request_token()
    )
    if is_response_valid(
        auth_group_response, "Auth group API could not fetch the data!"
    ):
        auth_group_data = is_response_empty(
            auth_group_response.json()[0], True, "Auth group record does not exist!"
        )
        return auth_group_data


def get_batch_from_group(group_id):
    response = requests.get(
        group_db_url, params={"id": group_id}, headers=db_request_token()
    )
    if is_response_valid(response, "Group API could not fetch the data!"):
        batch_data = is_response_empty(
            response.json()[0], True, "Group record does not exist!"
        )
        if batch_data:
            return get_auth_group_details(batch_data["child_id"]["auth_group_id"])


@router.get("/{session_id}")
def get_group_for_session(session_id: str):
    response = requests.get(
        group_session_db_url,
        params={"session_id": session_id},
        headers=db_request_token(),
    )
    if is_response_valid(response, "Group Session API could not fetch the data!"):
        group_session_data = is_response_empty(
            response.json()[0], True, "Group Session record does not exist!"
        )
        if group_session_data:
            return get_batch_from_group(group_session_data["group_id"])
