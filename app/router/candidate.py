from fastapi import APIRouter, Request
import requests
from routes import candidate_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from mapping import (
    USER_QUERY_PARAMS,
    CANDIDATE_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
)
from logger_config import get_logger
from services.candidate_service import (
    create_candidate as create_candidate_service,
    verify_candidate_comprehensive,
)

router = APIRouter(prefix="/candidate", tags=["Candidate"])
logger = get_logger()


@router.get("/")
def get_candidates(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        CANDIDATE_QUERY_PARAMS + USER_QUERY_PARAMS + ENROLLMENT_RECORD_PARAMS,
    )

    logger.info(f"Fetching candidates with params: {query_params}")

    response = requests.get(
        candidate_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Candidate API could not fetch the candidate!"):
        candidates_data = is_response_empty(
            response.json(), True, "Candidate does not exist"
        )
        logger.info("Successfully retrieved candidate data")
        return candidates_data


@router.get("/verify")
async def verify_candidate(request: Request, candidate_id: str):
    """Verify candidate"""
    query_params = validate_and_build_query_params(
        request.query_params, CANDIDATE_QUERY_PARAMS + USER_QUERY_PARAMS
    )

    return await verify_candidate_comprehensive(candidate_id, query_params)


@router.post("/")
async def create_candidate(request: Request):
    return await create_candidate_service(request)
