"""Teacher service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import teacher_db_url
from app.helpers import db_request_token, is_response_valid, safe_get_first_item
from app.mapping import TEACHER_QUERY_PARAMS

logger = get_logger()


def get_teacher_by_id(teacher_id: str) -> Optional[Dict[str, Any]]:
    """Get teacher by teacher_id."""
    return get_teachers(teacher_id=teacher_id)


def get_teachers(**params) -> Optional[Dict[str, Any]]:
    """Get teachers with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v for k, v in params.items() if v is not None and k in TEACHER_QUERY_PARAMS
    }

    logger.info(f"Fetching teachers with params: {query_params}")

    response = requests.get(
        teacher_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Teacher API could not fetch the data!"):
        teacher_data = safe_get_first_item(response.json(), "Teacher does not exist!")
        logger.info("Successfully retrieved teacher data")
        return teacher_data

    return None
