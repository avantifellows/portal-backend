from fastapi import APIRouter, HTTPException
import requests
from settings import settings
from models import UserSession

router = APIRouter(prefix="/user-session", tags=["User-Session"])
user_session_db_url = settings.db_url + "/user-session/"


@router.post("/")
def user_session_data(user_session: UserSession):
    """
    This API writes user interaction details corresponding to a session ID.
    """
    response = requests.post(user_session_db_url, data=user_session)
    return response
