from fastapi import APIRouter, Request, HTTPException
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
    SCHOOL_QUERY_PARAMS,
)
from app.services.teacher_service import verify_teacher_by_id
from app.services.subject_service import get_subject_by_name
from app.services.group_user_service import (
    create_auth_group_user_record,
    create_batch_user_record,
    create_school_user_record,
)
from app.logger_config import get_logger

router = APIRouter(prefix="/teacher", tags=["Teacher"])
logger = get_logger()


def create_new_teacher_record(data):
    """Create new teacher record with proper error handling"""
    try:
        logger.info("Creating new teacher record")

        response = requests.post(teacher_db_url, json=data, headers=db_request_token())

        if is_response_valid(response, "Teacher API could not post the data!"):
            try:
                response_data = response.json()
                created_teacher_data = is_response_empty(
                    response_data,
                    True,
                    "Teacher API could not fetch the created teacher",
                )

                logger.info("Successfully created teacher record")
                return created_teacher_data
            except ValueError as json_error:
                logger.error(f"Failed to parse JSON response: {json_error}")
                logger.error(f"Response content: {response.text}")
                raise HTTPException(
                    status_code=500, detail="Invalid JSON response from teacher API"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating teacher record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating teacher record")


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


@router.post("/")
async def create_teacher(request: Request):
    """Thin router layer - delegates to service."""
    from app.services.teacher_service import create_teacher as create_teacher_service

    return await create_teacher_service(request)
