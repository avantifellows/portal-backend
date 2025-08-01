from fastapi import APIRouter, Request
import requests
from app.routes import group_user_db_url
from app.router import enrollment_record
from app.helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from app.mapping import GROUP_USER_QUERY_PARAMS
from app.logger_config import get_logger

router = APIRouter(prefix="/group-user", tags=["Group-User"])
logger = get_logger()


def create_auth_group_enrollment_record(data):
    enrollment_record.create_enrollment_record()


@router.get("/")
def get_group_user(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, GROUP_USER_QUERY_PARAMS
    )

    logger.info(f"Fetching group-user with params: {query_params}")

    response = requests.get(
        group_user_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Group-User API could not fetch the data!"):
        group_user_data = is_response_empty(
            response.json(), True, "Group-User record does not exist!"
        )
        logger.info("Successfully retrieved group-user data")
        return group_user_data


@router.post("/")
async def create_group_user(request: Request):
    data = await request.body()

    logger.info(f"Creating group-user with data length: {len(data)} bytes")

    response = requests.post(group_user_db_url, data=data, headers=db_request_token())

    if is_response_valid(response, "Group-User API could not post the data!"):
        created_data = is_response_empty(
            response.json(), True, "Group-User API could not fetch the created record!"
        )
        logger.info("Successfully created group-user record")
        return created_data
