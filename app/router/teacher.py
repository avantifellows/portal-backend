from fastapi import APIRouter, Request
import requests
from routes import teacher_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from mapping import (
    USER_QUERY_PARAMS,
    TEACHER_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
    SCHOOL_QUERY_PARAMS,
)
from services.teacher_service import (
    verify_teacher_comprehensive,
    create_teacher as create_teacher_service,
)
from logger_config import get_logger

router = APIRouter(prefix="/teacher", tags=["Teacher"])
logger = get_logger()


@router.get("/")
def get_teachers(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        TEACHER_QUERY_PARAMS
        + USER_QUERY_PARAMS
        + ENROLLMENT_RECORD_PARAMS
        + SCHOOL_QUERY_PARAMS,
    )

    logger.info(f"Fetching teachers with params: {query_params}")

    response = requests.get(
        teacher_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Teacher API could not fetch the teacher!"):
        teachers_data = is_response_empty(
            response.json(), True, "Teacher does not exist"
        )
        logger.info("Successfully retrieved teacher data")
        return teachers_data


@router.get("/verify")
async def verify_teacher(request: Request, teacher_id: str):
    """Verify teacher"""
    query_params = validate_and_build_query_params(
        request.query_params, TEACHER_QUERY_PARAMS + USER_QUERY_PARAMS
    )

    return await verify_teacher_comprehensive(teacher_id, query_params)


@router.post("/")
async def create_teacher(request: Request):
    return await create_teacher_service(request)
