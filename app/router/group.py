from fastapi import APIRouter, Request
import requests
from app.routes import group_db_url
from app.helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from app.mapping import GROUP_QUERY_PARAMS

router = APIRouter(prefix="/group", tags=["Group"])


@router.get("/")
def get_group(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, GROUP_QUERY_PARAMS
    )
    response = requests.get(
        group_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "Group API could not fetch the data!"):
        return is_response_empty(response.json(), True, "Group record does not exist!")
