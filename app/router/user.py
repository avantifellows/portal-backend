from fastapi import APIRouter, Request, HTTPException
from services.student_service import create_student, get_students
from services.teacher_service import create_teacher, get_teacher_by_id
from services.candidate_service import create_candidate, get_candidate_by_id
from services.token_service import tokens_for_record
from helpers import safe_get_first_item
from helpers import (
    validate_and_build_query_params,
)
from mapping import (
    USER_QUERY_PARAMS,
    STUDENT_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
    SCHOOL_QUERY_PARAMS,
    TEACHER_QUERY_PARAMS,
    CANDIDATE_QUERY_PARAMS,
)
from logger_config import get_logger

router = APIRouter(prefix="/user", tags=["User"])
logger = get_logger()


def _fetch_created_record(user_type: str, response: dict, auth_group: str):
    if user_type == "student" and response.get("user_id"):
        return get_students(user_id=response["user_id"], auth_group=auth_group)
    if user_type == "teacher" and response.get("teacher_id"):
        return get_teacher_by_id(response["teacher_id"])
    if user_type == "candidate" and response.get("candidate_id"):
        return get_candidate_by_id(response["candidate_id"])
    return None


def with_session_tokens(response: dict, user_type: str, auth_group: str) -> dict:
    if not isinstance(response, dict) or not auth_group:
        return response
    if response.get("already_exists"):
        return response
    try:
        record = safe_get_first_item(
            _fetch_created_record(user_type, response, auth_group)
        )
        response.update(tokens_for_record(record, user_type, response, auth_group))
    except Exception as e:
        logger.warning(f"Could not issue session tokens after signup: {e}")
    return response


@router.post("/")
async def create_user(request: Request):
    try:
        data = await request.json()
        logger.info(
            f"Creating user with type: {data.get('user_type', 'unknown')} and auth_group: {data.get('auth_group', 'unknown')}"
        )

        # Validate form data
        if "form_data" not in data:
            raise HTTPException(status_code=400, detail="form_data is required")

        validate_and_build_query_params(
            data["form_data"],
            STUDENT_QUERY_PARAMS
            + USER_QUERY_PARAMS
            + ENROLLMENT_RECORD_PARAMS
            + SCHOOL_QUERY_PARAMS
            + TEACHER_QUERY_PARAMS
            + CANDIDATE_QUERY_PARAMS
            + [
                "id_generation",
                "user_type",
                "region",
                "batch_registration",
            ],
        )

        if data.get("user_type") == "student":
            # Create the student data payload
            student_data = {
                "form_data": data["form_data"],
                "id_generation": data.get("id_generation", False),
                "auth_group": data.get("auth_group", ""),
            }

            # Call create_student service function directly with the data
            create_student_response = await create_student(student_data)

            if not create_student_response:
                logger.error("Failed to create student - no response received")
                raise HTTPException(status_code=500, detail="Failed to create student")

            already_exists = create_student_response.get("already_exists", False)

            logger.info(f"Student creation result - Already exists: {already_exists}")

            return with_session_tokens(
                create_student_response, "student", data.get("auth_group", "")
            )
        elif data.get("user_type") == "teacher":
            teacher_data = {
                "form_data": data["form_data"],
                "id_generation": data.get("id_generation", False),
                "auth_group": data.get("auth_group", ""),
            }

            create_teacher_response = await create_teacher(teacher_data)

            if not create_teacher_response:
                logger.error("Failed to create teacher - no response received")
                raise HTTPException(status_code=500, detail="Failed to create teacher")

            already_exists = create_teacher_response.get("already_exists", False)

            logger.info(f"Teacher creation result - Already exists: {already_exists}")

            return with_session_tokens(
                create_teacher_response, "teacher", data.get("auth_group", "")
            )
        elif data.get("user_type") == "candidate":
            candidate_data = {
                "form_data": data["form_data"],
                "id_generation": data.get("id_generation", False),
                "auth_group": data.get("auth_group", ""),
            }
            create_candidate_response = await create_candidate(candidate_data)
            if not create_candidate_response:
                logger.error("Failed to create candidate - no response received")
                raise HTTPException(
                    status_code=500, detail="Failed to create candidate"
                )

            already_exists = create_candidate_response.get("already_exists", False)

            logger.info(f"Candidate creation result - Already exists: {already_exists}")

            return with_session_tokens(
                create_candidate_response, "candidate", data.get("auth_group", "")
            )
        else:
            logger.warning(f"Unsupported user type: {data.get('user_type')}")
            raise HTTPException(status_code=400, detail="Unsupported user type")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating user")
