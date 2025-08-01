"""Auth Group service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import auth_group_db_url
from app.helpers import db_request_token, is_response_valid, safe_get_first_item
from app.mapping import AUTH_GROUP_QUERY_PARAMS

logger = get_logger()


def get_auth_group_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get auth group by name."""
    return get_auth_group(name=name)


def get_auth_group_by_id(auth_group_id: str) -> Optional[Dict[str, Any]]:
    """Get auth group by ID."""
    return get_auth_group(id=auth_group_id)


def get_auth_group(**params) -> Optional[Dict[str, Any]]:
    """Get auth group with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v
        for k, v in params.items()
        if v is not None and k in AUTH_GROUP_QUERY_PARAMS
    }

    logger.info(f"Fetching auth group with params: {query_params}")

    response = requests.get(
        auth_group_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Auth Group API could not fetch the data!"):
        auth_group_data = safe_get_first_item(
            response.json(), "Auth Group does not exist!"
        )
        logger.info("Successfully retrieved auth group data")
        return auth_group_data

    return None
