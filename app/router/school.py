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

    response = requests.get(
        school_db_url,
        params={"code": code},
        headers=db_request_token(),
    )

    if is_response_valid(response):
        data = is_response_empty(response.json(), False)

        if data:
            # Safely get first item if data is a list
            school_data = safe_get_first_item(data) if isinstance(data, list) else data

            if not school_data:
                logger.warning(f"No school data found for code: {code}")
                return False

            for key, value in query_params.items():
                if key in USER_QUERY_PARAMS:
                    # Safe access to nested user object
                    user_data = school_data.get("user", {})
                    if not isinstance(user_data, dict):
                        logger.warning(
                            f"Invalid user data structure for school code: {code}"
                        )
                        return False
                    if user_data.get(key) != value:
                        logger.info(f"User verification failed for key: {key}")
                        return False

                if key in SCHOOL_QUERY_PARAMS:
                    if school_data.get(key) != value:
                        logger.info(f"School verification failed for key: {key}")
                        return False

            logger.info(f"School verification successful for code: {code}")
            return True

    logger.warning(f"School verification failed for code: {code}")
    return False
