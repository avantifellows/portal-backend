from fastapi import APIRouter, Request
import requests
from routes import school_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
    safe_get_first_item,
)
from mapping import SCHOOL_QUERY_PARAMS, USER_QUERY_PARAMS
from logger_config import get_logger

router = APIRouter(prefix="/school", tags=["School"])
logger = get_logger()


@router.get("/")
def get_school(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, SCHOOL_QUERY_PARAMS
    )

    logger.info(f"Fetching school with params: {query_params}")

    response = requests.get(
        school_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "School API could not fetch the data!"):
        # Use safe_get_first_item instead of direct array access
        school_data = safe_get_first_item(response.json(), "School does not exist")
        return school_data


@router.get("/verify")
async def verify_school(request: Request, code: str):
    query_params = validate_and_build_query_params(
        request.query_params, SCHOOL_QUERY_PARAMS + USER_QUERY_PARAMS
    )

    logger.info(f"Verifying school with code: {code} and params: {query_params}")

    # Try school code first
    school_record = None
    found_via_udise_code = False

    response = requests.get(
        school_db_url,
        params={"code": code},
        headers=db_request_token(),
    )

    if is_response_valid(response):
        data = is_response_empty(response.json(), False)
        if data:
            school_record = (
                safe_get_first_item(data) if isinstance(data, list) else data
            )

    # If no school found with school code, try udise_code
    if not school_record:
        logger.info(f"No school found with code, trying udise_code for: {code}")

        response = requests.get(
            school_db_url,
            params={"udise_code": code},
            headers=db_request_token(),
        )

        if is_response_valid(response):
            data = is_response_empty(response.json(), False)
            if data:
                school_record = (
                    safe_get_first_item(data) if isinstance(data, list) else data
                )
                found_via_udise_code = True

    # Now verify the school record against all query params
    if not school_record:
        logger.warning(f"No school found for code: {code}")
        return False

    # Verify all query parameters
    for key, value in query_params.items():
        if key in USER_QUERY_PARAMS:
            # Safe access to nested user object
            user_data = school_record.get("user", {})
            if not isinstance(user_data, dict):
                logger.warning(f"Invalid user data structure for school code: {code}")
                return False
            if user_data.get(key) != value:
                logger.info(f"User verification failed for key: {key}")
                return False

        elif key in SCHOOL_QUERY_PARAMS:
            # Skip code verification if we found the school via udise_code
            if key == "code" and found_via_udise_code:
                logger.info("Skipping code verification - found via udise_code")
                continue
            if school_record.get(key) != value:
                logger.info(f"School verification failed for key: {key}")
                return False

    logger.info(f"School verification successful for code: {code}")
    return True
