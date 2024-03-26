from fastapi import APIRouter, Request
import requests
from settings import settings
from routes import teacher_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from mapping import USER_QUERY_PARAMS, TEACHER_QUERY_PARAMS, ENROLLMENT_RECORD_PARAMS

router = APIRouter(prefix="/teacher", tags=["Teacher"])


@router.get("/")
def get_teachers(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        TEACHER_QUERY_PARAMS + USER_QUERY_PARAMS + ENROLLMENT_RECORD_PARAMS,
    )
    response = requests.get(
        teacher_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "Teacher API could not fetch the teacher!"):
        return is_response_empty(response.json(), True, "Teacher does not exist")


@router.get("/verify")
async def verify_teacher(request: Request, teacher_id: str):
    query_params = validate_and_build_query_params(
        request.query_params, TEACHER_QUERY_PARAMS + USER_QUERY_PARAMS
    )

    response = requests.get(
        teacher_db_url,
        params={"teacher_id": teacher_id},
        headers=db_request_token(),
    )

    if is_response_valid(response):
        data = is_response_empty(response.json(), False)

        if data:
            data = data[0]
            for key, value in query_params.items():
                if key in USER_QUERY_PARAMS and data["user"].get(key) != value:
                    return False
                if key in TEACHER_QUERY_PARAMS and data.get(key) != value:
                    return False
            return True

    return False
