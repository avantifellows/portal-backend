"""Form service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import form_db_url
from app.helpers import db_request_token, is_response_valid, safe_get_first_item
from app.mapping import FORM_SCHEMA_QUERY_PARAMS

logger = get_logger()


def get_form_schema_by_id(form_id: str) -> Optional[Dict[str, Any]]:
    """Get form schema by ID."""
    return get_form_schema(id=form_id)


def get_form_schema(**params) -> Optional[Dict[str, Any]]:
    """Get form schema with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v
        for k, v in params.items()
        if v is not None and k in FORM_SCHEMA_QUERY_PARAMS
    }

    logger.info(f"Fetching form schema with params: {query_params}")

    response = requests.get(
        form_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Form API could not fetch the data!"):
        form_data = safe_get_first_item(response.json(), "Form schema does not exist!")
        logger.info("Successfully retrieved form schema")
        return form_data

    return None
