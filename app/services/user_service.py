"""User service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from logger_config import get_logger
from routes import user_db_url
from helpers import db_request_token, is_response_valid, is_response_empty
from mapping import USER_QUERY_PARAMS

logger = get_logger()


def get_users(**params) -> Optional[Dict[str, Any]]:
    """Get users with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v for k, v in params.items() if v is not None and k in USER_QUERY_PARAMS
    }

    logger.info(f"Fetching users with params: {query_params}")

    response = requests.get(
        user_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "User API could not fetch the data!"):
        user_data = is_response_empty(response.json(), False)
        logger.info("Successfully retrieved user data")
        return user_data

    return None


def get_user_by_email_and_phone(
    email: str = None, phone: str = None
) -> Optional[Dict[str, Any]]:
    """Get user by email and/or phone."""
    params = {}
    if email:
        params["email"] = email
    if phone:
        params["phone"] = phone
    return get_users(**params)
