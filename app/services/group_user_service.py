"""Group User service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import group_user_db_url
from app.helpers import db_request_token, is_response_valid
from app.settings import settings

logger = get_logger()


async def create_group_user(group_id: str, user_id: str, academic_year: str = None, start_date: str = None) -> Optional[Dict[str, Any]]:
    """Create group user record."""
    data = {
        "group_id": group_id,
        "user_id": user_id,
        "academic_year": academic_year or settings.DEFAULT_ACADEMIC_YEAR
    }
    
    if start_date:
        data["start_date"] = start_date
    
    logger.info(f"Creating group user record: {data}")
    
    response = requests.post(
        group_user_db_url, data=data, headers=db_request_token()
    )
    
    if is_response_valid(response, "Group User API could not create the record!"):
        result = response.json()
        logger.info("Successfully created group user record")
        return result
    
    return None


def get_group_user(**params) -> Optional[Dict[str, Any]]:
    """Get group user with flexible parameters."""
    # Filter out None values
    query_params = {k: v for k, v in params.items() if v is not None}
    
    logger.info(f"Fetching group user with params: {query_params}")
    
    response = requests.get(
        group_user_db_url, params=query_params, headers=db_request_token()
    )
    
    if is_response_valid(response, "Group User API could not fetch the data!"):
        result = response.json()
        logger.info("Successfully retrieved group user data")
        return result
    
    return None