from fastapi import APIRouter
import requests
from models import UserSession
from datetime import datetime
from routes import user_session_db_url
from helpers import db_request_token, is_response_valid, is_response_empty

router = APIRouter(prefix="/user-session", tags=["User-Session"])


@router.post("/")
def user_session(user_session: UserSession):
    query_params = user_session.dict()
    query_params["timestamp"] = datetime.now().isoformat()
    response = requests.post(
        user_session_db_url, json=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "User-session API could not post the data!"):
        is_response_empty(
            response.json(), "User-session API could not fetch the created record!"
        )
