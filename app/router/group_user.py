from fastapi import APIRouter, Request
import requests
from routes import group_user_db_url
from router import enrollment_record
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from mapping import GROUP_USER_QUERY_PARAMS

router = APIRouter(prefix="/group-user", tags=["Group-User"])


def create_auth_group_enrollment_record(data):
    enrollment_record.create_enrollment_record()


@router.get("/")
def get_group_user(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, GROUP_USER_QUERY_PARAMS
    )
    response = requests.get(
        group_user_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "Group-User API could not fetch the data!"):
        return is_response_empty(
            response.json(), True, "Group-User record does not exist!"
        )


@router.post("/")
async def create_group_user(request: Request):
    data = await request.body()
    response = requests.post(group_user_db_url, data=data, headers=db_request_token())
    if is_response_valid(response, "Group-User API could not post the data!"):
        return is_response_empty(
            response.json(), True, "Group-User API could not fetch the created record!"
        )
