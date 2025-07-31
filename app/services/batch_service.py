"""Batch service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import batch_db_url
from app.helpers import db_request_token, is_response_valid, safe_get_first_item
from app.mapping import BATCH_QUERY_PARAMS

logger = get_logger()


def get_batch_by_id(batch_id: str) -> Optional[Dict[str, Any]]:
    """Get batch by ID."""
    return get_batch(batch_id=batch_id)


def get_batch(**params) -> Optional[Dict[str, Any]]:
    """Get batch with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {k: v for k, v in params.items() if v is not None and k in BATCH_QUERY_PARAMS}
    
    logger.info(f"Fetching batch with params: {query_params}")
    
    response = requests.get(
        batch_db_url, params=query_params, headers=db_request_token()
    )
    
    if is_response_valid(response, "Batch API could not fetch the data!"):
        batch_data = safe_get_first_item(response.json(), "Batch does not exist!")
        logger.info("Successfully retrieved batch data")
        return batch_data
    
    return None