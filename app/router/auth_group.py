from fastapi import APIRouter, Request
import requests
from models import AuthGroupResponse
from routes import auth_group_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    safe_get_first_item,
)
from mapping import AUTH_GROUP_QUERY_PARAMS
from logger_config import get_logger

router = APIRouter(prefix="/auth-group", tags=["Auth-Group"])
logger = get_logger()


@router.get("/", response_model=AuthGroupResponse)
def get_auth_group(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, AUTH_GROUP_QUERY_PARAMS
    )

    logger.info(f"Fetching auth group with params: {query_params}")

    response = requests.get(
        auth_group_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Auth Group API could not fetch the data!"):
        # Use safe_get_first_item instead of direct array access
        auth_group_data = safe_get_first_item(
            response.json(), "Auth Group record does not exist!"
        )
        logger.info("Successfully retrieved auth group data")
        return auth_group_data
