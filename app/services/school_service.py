"""School service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import school_db_url
from app.helpers import db_request_token, is_response_valid, safe_get_first_item
from app.mapping import SCHOOL_QUERY_PARAMS

logger = get_logger()


def get_school_by_name_and_region(name: str, region: str) -> Optional[Dict[str, Any]]:
    """Get school by name and region."""
    return get_school(name=name, region=region)


def get_school_by_name_and_district(
    name: str, district: str
) -> Optional[Dict[str, Any]]:
    """Get school by name and district."""
    return get_school(name=name, district=district)


def get_school_by_name_district_state(
    name: str, district: str, state: str
) -> Optional[Dict[str, Any]]:
    """Get school by name, district, and state."""
    return get_school(name=name, district=district, state=state)


def get_school_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Get school by code."""
    return get_school(code=code)


def get_school(**params) -> Optional[Dict[str, Any]]:
    """Get school with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v for k, v in params.items() if v is not None and k in SCHOOL_QUERY_PARAMS
    }

    logger.info(f"Fetching school with params: {query_params}")

    response = requests.get(
        school_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "School API could not fetch the data!"):
        school_data = safe_get_first_item(response.json(), "School does not exist!")
        logger.info("Successfully retrieved school data")
        return school_data

    return None
