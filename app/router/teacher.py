from fastapi import APIRouter, Request
from helpers import validate_and_build_query_params
from mapping import USER_QUERY_PARAMS, TEACHER_QUERY_PARAMS
from services.teacher_service import (
    verify_teacher_comprehensive,
    create_teacher as create_teacher_service,
)
from logger_config import get_logger

router = APIRouter(prefix="/teacher", tags=["Teacher"])
logger = get_logger()


@router.get("/verify")
async def verify_teacher(request: Request, teacher_id: str):
    """Verify teacher"""
    query_params = validate_and_build_query_params(
        request.query_params,
        TEACHER_QUERY_PARAMS + USER_QUERY_PARAMS + ["auth_group", "auth_group_id"],
    )

    return await verify_teacher_comprehensive(teacher_id, query_params)


@router.post("/")
async def create_teacher(request: Request):
    return await create_teacher_service(request)
