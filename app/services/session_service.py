"""Session service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import session_db_url
from app.helpers import db_request_token, is_response_valid, safe_get_first_item
from app.mapping import SESSION_QUERY_PARAMS

logger = get_logger()


def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by session_id."""
    return get_session(session_id=session_id)


async def get_session(**params) -> Optional[Dict[str, Any]]:
    """Get session with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v for k, v in params.items() if v is not None and k in SESSION_QUERY_PARAMS
    }

    logger.info(f"Fetching session with params: {query_params}")

    response = requests.get(
        session_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Session API could not fetch the data!"):
        session_data = safe_get_first_item(response.json(), "Session does not exist!")
        logger.info("Successfully retrieved session data")
        return session_data

    return None
