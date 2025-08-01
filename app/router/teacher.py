from fastapi import APIRouter, Request
import requests
from app.routes import teacher_db_url
from app.helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
    safe_get_first_item,
)
from app.mapping import (
    USER_QUERY_PARAMS,
    TEACHER_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
)
from app.logger_config import get_logger

router = APIRouter(prefix="/teacher", tags=["Teacher"])
logger = get_logger()


@router.get("/")
def get_teachers(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        TEACHER_QUERY_PARAMS + USER_QUERY_PARAMS + ENROLLMENT_RECORD_PARAMS,
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
    query_params = validate_and_build_query_params(
        request.query_params, TEACHER_QUERY_PARAMS + USER_QUERY_PARAMS
    )

    logger.info(f"Verifying teacher: {teacher_id} with params: {query_params}")

    response = requests.get(
        teacher_db_url,
        params={"teacher_id": teacher_id},
        headers=db_request_token(),
    )

    if is_response_valid(response):
        data = is_response_empty(response.json(), False)

        if data:
            # Safe access to first teacher
            teacher_record = (
                safe_get_first_item(data) if isinstance(data, list) else data
            )

            if not teacher_record:
                logger.warning(f"No teacher data found for teacher_id: {teacher_id}")
                return False

            for key, value in query_params.items():
                if key in USER_QUERY_PARAMS:
                    # Safe access to nested user object
                    user_data = teacher_record.get("user", {})
                    if not isinstance(user_data, dict):
                        logger.warning(
                            f"Invalid user data structure for teacher: {teacher_id}"
                        )
                        return False
                    if user_data.get(key) != value:
                        logger.info(f"User verification failed for key: {key}")
                        return False

                if key in TEACHER_QUERY_PARAMS:
                    if teacher_record.get(key) != value:
                        logger.info(f"Teacher verification failed for key: {key}")
                        return False

            logger.info(f"Teacher verification successful for: {teacher_id}")
            return True

    logger.warning(f"Teacher verification failed for: {teacher_id}")
    return False
