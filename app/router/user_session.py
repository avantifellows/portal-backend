from fastapi import APIRouter
import requests
from models import UserSession
from datetime import datetime
from routes import user_session_db_url
from helpers import db_request_token, is_response_valid, is_response_empty
from router import student, session, user
from request import build_request

router = APIRouter(prefix="/user-session", tags=["User-Session"])


@router.post("/")
async def user_session(user_session: UserSession):
    query_params = user_session.dict()
    query_params["timestamp"] = datetime.now().isoformat()

    if query_params["user_type"] == "student":
        user_id_response = student.get_students(
            build_request(query_params={"student_id": query_params["user_id"]})
        )

    query_params["user_id"] = user_id_response[0]["user"]["id"]

    session_pk_id_response = await session.get_session(
        build_request(query_params={"session_id": query_params["session_id"]})
    )
    query_params["session_id"] = session_pk_id_response[0]["id"]

    response = requests.post(
        user_session_db_url, json=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "User-session API could not post the data!"):
        is_response_empty(
            response.json(), "User-session API could not fetch the created record!"
        )
