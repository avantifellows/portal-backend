from fastapi import APIRouter, Request
from helpers import validate_and_build_query_params
from mapping import USER_QUERY_PARAMS, CANDIDATE_QUERY_PARAMS
from logger_config import get_logger
from services.candidate_service import verify_candidate_comprehensive

router = APIRouter(prefix="/candidate", tags=["Candidate"])
logger = get_logger()


@router.get("/verify")
async def verify_candidate(request: Request, candidate_id: str):
    """Verify candidate"""
    query_params = validate_and_build_query_params(
        request.query_params,
        CANDIDATE_QUERY_PARAMS + USER_QUERY_PARAMS + ["auth_group", "auth_group_id"],
    )

    return await verify_candidate_comprehensive(candidate_id, query_params)
