from fastapi import APIRouter, HTTPException, Request
import requests
from services.student_service import (
    create_student as create_student_service,
    verify_student_comprehensive,
    complete_profile_details_service,
    patch_student_service,
)
from routes import student_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from logger_config import get_logger
from mapping import (
    USER_QUERY_PARAMS,
    STUDENT_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
)

router = APIRouter(prefix="/student", tags=["Student"])
logger = get_logger()


@router.get("/")
def get_students(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        STUDENT_QUERY_PARAMS + USER_QUERY_PARAMS + ENROLLMENT_RECORD_PARAMS,
    )

    logger.info(f"Fetching students with params: {query_params}")

    response = requests.get(
        student_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Student API could not fetch the student!"):
        students_data = is_response_empty(
            response.json(), False, "Student does not exist"
        )
        logger.info(
            f"Successfully retrieved {len(students_data) if isinstance(students_data, list) else 1} student(s)"
        )
        return students_data


@router.get("/verify")
async def verify_student(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        STUDENT_QUERY_PARAMS + USER_QUERY_PARAMS + ["auth_group_id"],
    )

    return await verify_student_comprehensive(query_params)


@router.post("/")
async def create_student(request: Request):
    return await create_student_service(request)


@router.patch("/")
async def update_student(request: Request):
    try:
        data = await request.json()
        return await patch_student_service(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_student router: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating student")


@router.post("/complete-profile-details")
async def complete_profile_details(request: Request):
    try:
        data = await request.json()
        return await complete_profile_details_service(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete_profile_details router: {str(e)}")
        raise HTTPException(status_code=500, detail="Error completing profile details")
