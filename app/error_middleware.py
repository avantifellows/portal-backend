from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from logger_config import get_logger
import traceback
from typing import Union
import requests

logger = get_logger()


async def error_handling_middleware(request: Request, call_next):
    """
    Middleware to catch and handle common errors gracefully
    """
    try:
        response = await call_next(request)
        return response
    except HTTPException:
        # Re-raise HTTP exceptions as they are already handled
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Database connection error for {request.url}: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database service unavailable. Please try again later.",
                "error_type": "connection_error",
            },
        )
    except requests.exceptions.Timeout as e:
        logger.error(f"Database timeout error for {request.url}: {str(e)}")
        return JSONResponse(
            status_code=504,
            content={
                "detail": "Database request timed out. Please try again later.",
                "error_type": "timeout_error",
            },
        )
    except IndexError as e:
        logger.error(f"Index error for {request.url}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Requested resource not found.",
                "error_type": "index_error",
            },
        )
    except KeyError as e:
        logger.error(f"Key error for {request.url}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=400,
            content={
                "detail": f"Missing required field: {str(e)}",
                "error_type": "key_error",
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error for {request.url}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred. Please try again later.",
                "error_type": "internal_error",
            },
        )


def validate_response_structure(
    response_data: Union[list, dict, None], expected_type: str = "any"
):
    """
    Validate the structure of API response data
    """
    if response_data is None:
        return False, "Response data is None"

    if expected_type == "list" and not isinstance(response_data, list):
        return False, f"Expected list but got {type(response_data)}"

    if expected_type == "dict" and not isinstance(response_data, dict):
        return False, f"Expected dict but got {type(response_data)}"

    if (
        expected_type == "list"
        and isinstance(response_data, list)
        and len(response_data) == 0
    ):
        return False, "Response list is empty"

    return True, "Valid response structure"


def safe_dict_access(data: dict, key: str, default=None):
    """
    Safely access dictionary keys with logging
    """
    if not isinstance(data, dict):
        logger.warning(
            f"Attempted to access key '{key}' on non-dict object: {type(data)}"
        )
        return default

    return data.get(key, default)
