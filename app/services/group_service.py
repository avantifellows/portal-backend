"""Group service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import group_db_url
from app.helpers import db_request_token, is_response_valid, safe_get_first_item
from app.mapping import GROUP_QUERY_PARAMS

logger = get_logger()


def get_group_by_child_id_and_type(
    child_id: str, group_type: str
) -> Optional[Dict[str, Any]]:
    """Get group by child_id and type."""
    return get_group(child_id=child_id, type=group_type)


def get_group_by_id(group_id: str) -> Optional[Dict[str, Any]]:
    """Get group by ID."""
    return get_group(id=group_id)


def get_group(**params) -> Optional[Dict[str, Any]]:
    """Get group with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v for k, v in params.items() if v is not None and k in GROUP_QUERY_PARAMS
    }

    logger.info(f"Fetching group with params: {query_params}")

    response = requests.get(
        group_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Group API could not fetch the data!"):
        group_data = safe_get_first_item(response.json(), "Group does not exist!")
        logger.info("Successfully retrieved group data")
        return group_data

    return None
