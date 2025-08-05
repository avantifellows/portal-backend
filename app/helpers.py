from fastapi import HTTPException
from logger_config import get_logger
from settings import settings
from typing import Any, List, Dict, Union

logger = get_logger()


def is_response_valid(response, error_message=""):
    """Enhanced response validation with better error context"""
    if response.status_code in [200, 201]:
        return True

    # Log the actual response for debugging
    logger.error(
        f"API Response Error - Status: {response.status_code}, Content: {response.text}"
    )

    if error_message:
        logger.error(error_message)
        raise HTTPException(
            status_code=500, detail=f"{error_message} (Status: {response.status_code})"
        )
    return False


def is_response_empty(
    response_data: Union[List, Dict, Any], return_boolean: bool, error_message: str = ""
):
    """Enhanced response validation with proper type checking"""
    # Handle None response
    if response_data is None:
        if return_boolean:
            if error_message:
                logger.error(f"Empty response: {error_message}")
                raise HTTPException(status_code=404, detail=error_message)
            return False
        return []

    # Handle list responses
    if isinstance(response_data, list):
        if len(response_data) == 0:
            if return_boolean:
                if error_message:
                    logger.error(f"Empty list response: {error_message}")
                    raise HTTPException(status_code=404, detail=error_message)
                return False
            return []
        return response_data

    # Handle dict responses (single objects)
    if isinstance(response_data, dict):
        if not response_data:  # Empty dict
            if return_boolean:
                if error_message:
                    logger.error(f"Empty dict response: {error_message}")
                    raise HTTPException(status_code=404, detail=error_message)
                return False
            return []
        return response_data

    # Handle other truthy/falsy values
    if response_data:
        return response_data

    if return_boolean:
        if error_message:
            logger.error(f"Falsy response: {error_message}")
            raise HTTPException(status_code=404, detail=error_message)
        return False
    return []


def safe_get_first_item(response_data: Union[List, Dict, Any], error_message: str = ""):
    """Safely get the first item from a response, handling various data types"""
    if response_data is None:
        if error_message:
            logger.error(f"Cannot get first item from None: {error_message}")
            raise HTTPException(status_code=404, detail=error_message)
        return None

    if isinstance(response_data, list):
        if len(response_data) == 0:
            if error_message:
                logger.error(f"Cannot get first item from empty list: {error_message}")
                raise HTTPException(status_code=404, detail=error_message)
            return None
        return response_data[0]

    # If it's not a list, return as-is (could be a single dict)
    return response_data


def validate_and_build_query_params(data, valid_query_params):
    query_params = {key: data[key] for key in data.keys() if key in valid_query_params}
    invalid_params = [key for key in data.keys() if key not in valid_query_params]
    if invalid_params:
        raise HTTPException(
            status_code=400,
            detail="Query Parameter(s) {} is not allowed!".format(
                ", ".join(invalid_params)
            ),
        )
    return query_params


def db_request_token():
    return {"Authorization": f"Bearer {settings.TOKEN}"}
