from fastapi import APIRouter, Request, HTTPException
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
from logger_config import get_logger

router = APIRouter(prefix="/user", tags=["User"])
logger = get_logger()


@router.get("/")
def get_users(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, USER_QUERY_PARAMS
    )

    logger.info(f"Fetching users with params: {query_params}")

    response = requests.get(
        user_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "User API could not fetch the data!"):
        users_data = is_response_empty(response.json(), False, "User does not exist!")
        logger.info(
            f"Successfully retrieved {len(users_data) if isinstance(users_data, list) else 1} user(s)"
        )
        return users_data


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
            + [
                "id_generation",
                "user_type",
                "region",
                "batch_registration",
                "block_name",
            ],
        )

        if data.get("user_type") == "student":
            # Create the student data payload
            student_data = {
                "form_data": data["form_data"],
                "id_generation": data.get("id_generation", False),
                "auth_group": data.get("auth_group", ""),
            }

            # Call student.create_student directly with the data
            create_student_response = await student.create_student(student_data)

            if not create_student_response:
                logger.error("Failed to create student - no response received")
                raise HTTPException(status_code=500, detail="Failed to create student")

            student_id = create_student_response.get("student_id", "unknown")
            already_exists = create_student_response.get("already_exists", False)

            logger.info(
                f"Student creation result - ID: {student_id}, Already exists: {already_exists}"
            )

            return {
                "user_id": student_id,
                "already_exists": already_exists,
            }
        else:
            logger.warning(f"Unsupported user type: {data.get('user_type')}")
            raise HTTPException(status_code=400, detail="Unsupported user type")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating user")
