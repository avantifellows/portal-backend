from fastapi import APIRouter, HTTPException
import requests
from settings import settings
from models import UserSession
from datetime import datetime
from fastapi.responses import JSONResponse
import json

router = APIRouter(prefix="/user-session", tags=["User-Session"])
user_session_db_url = settings.db_url + "/user-session/"


@router.post("/")
def user_session_data(user_session: UserSession):
    """
    This API writes user interaction details corresponding to a session ID.
    """
    query_params = user_session.dict()
    query_params["start_time"] = datetime.now().isoformat()
    response = requests.post(user_session_db_url, json=query_params)
    if response.status_code == 201:
        return JSONResponse(status_code=201, content="Resource created successfully")
    raise HTTPException(status_code=500, detail="Resource could not be created!")
