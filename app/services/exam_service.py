"""Exam service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from logger_config import get_logger
from routes import exam_db_url
from helpers import db_request_token, is_response_valid, safe_get_first_item

logger = get_logger()


def get_exam_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get exam by name."""
    return get_exam(name=name)


def get_exam_by_id(exam_id: str) -> Optional[Dict[str, Any]]:
    """Get exam by ID."""
    return get_exam(id=exam_id)


def get_exam(**params) -> Optional[Dict[str, Any]]:
    """Get exam with flexible parameters."""
    # Filter out None values
    query_params = {k: v for k, v in params.items() if v is not None}

    logger.info(f"Fetching exam with params: {query_params}")

    response = requests.get(
        exam_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Exam API could not fetch the data!"):
        exam_data = safe_get_first_item(response.json(), "Exam record does not exist!")
        logger.info("Successfully retrieved exam data")
        return exam_data

    return None
