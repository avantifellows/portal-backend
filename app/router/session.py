from fastapi import APIRouter, HTTPException, Request
import requests
from app.settings import settings
from app.routes import session_db_url
from app.models import SessionResponse
from app.helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from app.mapping import SESSION_QUERY_PARAMS

router = APIRouter(prefix="/session", tags=["Session"])


@router.get("/", response_model=SessionResponse)
async def get_session(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, SESSION_QUERY_PARAMS
    )
    response = requests.get(
        session_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "Session API could not fetch the data!"):
        return is_response_empty(response.json(), "Session does not exist!")
