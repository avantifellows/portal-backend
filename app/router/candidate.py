from fastapi import APIRouter, Request, HTTPException
import requests
from routes import candidate_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
    safe_get_first_item,
)
from mapping import (
    USER_QUERY_PARAMS,
    CANDIDATE_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
)
from logger_config import get_logger
from services.candidate_service import create_candidate as create_candidate_service

router = APIRouter(prefix="/candidate", tags=["Candidate"])
logger = get_logger()


def create_new_candidate_record(data):
    """Create new candidate record with proper error handling"""
    try:
        logger.info("Creating new candidate record")

        response = requests.post(
            candidate_db_url, json=data, headers=db_request_token()
        )

        if is_response_valid(response, "Candidate API could not post the data!"):
            try:
                response_data = response.json()
                created_candidate_data = is_response_empty(
                    response_data,
                    True,
                    "Candidate API could not fetch the created candidate",
                )

                logger.info("Successfully created candidate record")
                return created_candidate_data
            except ValueError as json_error:
                logger.error(f"Failed to parse JSON response: {json_error}")
                logger.error(f"Response content: {response.text}")
                raise HTTPException(
                    status_code=500, detail="Invalid JSON response from candidate API"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating candidate record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating candidate record")


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
    query_params = validate_and_build_query_params(
        request.query_params, CANDIDATE_QUERY_PARAMS + USER_QUERY_PARAMS
    )

    logger.info(f"Verifying candidate: {candidate_id} with params: {query_params}")

    response = requests.get(
        candidate_db_url,
        params={"candidate_id": candidate_id},
        headers=db_request_token(),
    )

    if is_response_valid(response):
        data = is_response_empty(response.json(), False)

        if data:
            # Safe access to first candidate
            candidate_record = (
                safe_get_first_item(data) if isinstance(data, list) else data
            )

            if not candidate_record:
                logger.warning(
                    f"No candidate data found for candidate_id: {candidate_id}"
                )
                return False

            for key, value in query_params.items():
                if key in USER_QUERY_PARAMS:
                    # Safe access to nested user object
                    user_data = candidate_record.get("user", {})
                    if not isinstance(user_data, dict):
                        logger.warning(
                            f"Invalid user data structure for candidate: {candidate_id}"
                        )
                        return False
                    if user_data.get(key) != value:
                        logger.info(f"User verification failed for key: {key}")
                        return False

                if key in CANDIDATE_QUERY_PARAMS:
                    if candidate_record.get(key) != value:
                        logger.info(f"Candidate verification failed for key: {key}")
                        return False

            logger.info(f"Candidate verification successful for: {candidate_id}")
            return True

    logger.warning(f"Candidate verification failed for: {candidate_id}")
    return False


@router.post("/")
async def create_candidate(request: Request):
    """Thin router layer - delegates to service."""
    return await create_candidate_service(request)
