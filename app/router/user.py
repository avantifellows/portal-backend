from fastapi import APIRouter, Request, HTTPException
from services.student_service import create_student
from services.teacher_service import create_teacher
from services.candidate_service import create_candidate
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

            return create_student_response
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

            return create_teacher_response
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

            return create_candidate_response
        else:
            logger.warning(f"Unsupported user type: {data.get('user_type')}")
            raise HTTPException(status_code=400, detail="Unsupported user type")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating user")
