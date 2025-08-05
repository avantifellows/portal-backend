"""Subject service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import subject_db_url
from app.helpers import db_request_token, is_response_valid, safe_get_first_item

logger = get_logger()


def get_subject_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get subject by name."""
    return get_subject(name=name)


def get_subject_by_id(subject_id: str) -> Optional[Dict[str, Any]]:
    """Get subject by ID."""
    return get_subject(id=subject_id)


def get_subject(**params) -> Optional[Dict[str, Any]]:
    """Get subject with flexible parameters."""
    # Filter out None values
    query_params = {k: v for k, v in params.items() if v is not None}

    logger.info(f"Fetching subject with params: {query_params}")

    response = requests.get(
        subject_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Subject API could not fetch the data!"):
        subject_data = safe_get_first_item(response.json(), "Subject does not exist!")
        logger.info("Successfully retrieved subject data")
        return subject_data

    return None
