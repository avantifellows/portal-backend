from fastapi import APIRouter, Request
import requests
from models import AuthGroupResponse
from routes import auth_group_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from mapping import AUTH_GROUP_QUERY_PARAMS

router = APIRouter(prefix="/auth-group", tags=["Auth-Group"])


@router.get("/", response_model=AuthGroupResponse)
def get_auth_group(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, AUTH_GROUP_QUERY_PARAMS
    )
    response = requests.get(
        auth_group_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "Auth Group API could not fetch the data!"):
        return is_response_empty(
            response.json()[0], True, "Auth Group record does not exist!"
        )
