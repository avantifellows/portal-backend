"""Grade service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from logger_config import get_logger
from routes import grade_db_url
from helpers import db_request_token, is_response_valid, safe_get_first_item

logger = get_logger()


def get_grade_by_number(number: int) -> Optional[Dict[str, Any]]:
    """Get grade by number."""
    return get_grade(number=number)


def get_grade_by_id(grade_id: str) -> Optional[Dict[str, Any]]:
    """Get grade by ID."""
    return get_grade(id=grade_id)


def get_grade(**params) -> Optional[Dict[str, Any]]:
    """Get grade with flexible parameters."""
    # Filter out None values
    query_params = {k: v for k, v in params.items() if v is not None}

    logger.info(f"Fetching grade with params: {query_params}")

    response = requests.get(
        grade_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Grade API could not fetch the data!"):
        grade_data = safe_get_first_item(response.json(), "Grade does not exist!")
        logger.info("Successfully retrieved grade data")
        return grade_data

    return None
