from fastapi import APIRouter, Depends, HTTPException, Request
from services.student_service import (
    create_student as create_student_service,
    verify_student_comprehensive,
    complete_profile_details_service,
)
from router.auth import require_validated_session, session_user_id
from helpers import validate_and_build_query_params
from logger_config import get_logger
from mapping import USER_QUERY_PARAMS, STUDENT_QUERY_PARAMS

router = APIRouter(prefix="/student", tags=["Student"])
logger = get_logger()


@router.get("/verify")
async def verify_student(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        STUDENT_QUERY_PARAMS
        + USER_QUERY_PARAMS
        + ["auth_group", "auth_group_id", "otp"],
    )

    return await verify_student_comprehensive(query_params)


@router.post("/")
async def create_student(request: Request):
    return await create_student_service(request)


@router.post("/complete-profile-details")
async def complete_profile_details(
    request: Request, session: dict = Depends(require_validated_session)
):
    try:
        data = await request.json()
        # identity comes from the token, never from the body
        data.pop("student_id", None)
        data["user_id"] = session_user_id(session)
        data["auth_group"] = session.get("group")
        return await complete_profile_details_service(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete_profile_details router: {str(e)}")
        raise HTTPException(status_code=500, detail="Error completing profile details")
