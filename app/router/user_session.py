from fastapi import APIRouter, HTTPException
import requests
from settings import settings
from models import UserSession

router = APIRouter(prefix="/user-session", tags=["User-Session"])
user_session_db_url = settings.db_url + "/user-session/"

@router.post("/")
def user_session_data(user_session: UserSession):
    response = requests.post(user_session_db_url, data=user_session)
    if response.status_code != 200:
        return HTTPException(status_code=response.status_code, detail=response.errors)
