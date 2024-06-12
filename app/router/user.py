from fastapi import APIRouter, Request
import requests
from router import student
from request import build_request
from routes import user_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from mapping import (
    USER_QUERY_PARAMS,
    STUDENT_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
    SCHOOL_QUERY_PARAMS,
)

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/")
def get_users(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, USER_QUERY_PARAMS
    )
    response = requests.get(
        user_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "User API could not fetch the data!"):
        return is_response_empty(response.json(), False, "User does not exist!")


@router.post("/")
async def create_user(request: Request):
    data = await request.json()
    validate_and_build_query_params(
        data["form_data"],
        STUDENT_QUERY_PARAMS
        + USER_QUERY_PARAMS
        + ENROLLMENT_RECORD_PARAMS
        + SCHOOL_QUERY_PARAMS
        + ["id_generation", "user_type", "region"]
    )

    if data["user_type"] == "student":
        create_student_response = await student.create_student(
            build_request(
                body={
                    "form_data": data["form_data"],
                    "id_generation": data["id_generation"],
                    "auth_group": data["auth_group"],
                }
            )
        )
        return create_student_response
