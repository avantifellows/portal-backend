"""Student service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from app.logger_config import get_logger
from app.routes import student_db_url
from app.helpers import db_request_token, is_response_valid, is_response_empty
from app.mapping import (
    STUDENT_QUERY_PARAMS,
    USER_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
)

logger = get_logger()


def get_students(**params) -> Optional[Dict[str, Any]]:
    """Get students with flexible parameters."""
    # Filter out None values and validate against allowed params
    valid_params = STUDENT_QUERY_PARAMS + USER_QUERY_PARAMS + ENROLLMENT_RECORD_PARAMS
    query_params = {
        k: v for k, v in params.items() if v is not None and k in valid_params
    }

    logger.info(f"Fetching students with params: {query_params}")

    response = requests.get(
        student_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Student API could not fetch the data!"):
        student_data = is_response_empty(response.json(), False)
        logger.info("Successfully retrieved student data")
        return student_data

    return None


def get_student_by_id(student_id: str) -> Optional[Dict[str, Any]]:
    """Get student by student_id."""
    return get_students(student_id=student_id)


async def verify_student_by_id(student_id: str, **params) -> bool:
    """Verify student exists - simplified version for internal use."""
    try:
        student_data = get_students(student_id=student_id, **params)
        return bool(
            student_data and (isinstance(student_data, list) and len(student_data) > 0)
        )
    except Exception as e:
        logger.error(f"Error verifying student {student_id}: {str(e)}")
        return False


async def update_student_data(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update student record."""
    logger.info("Updating student record")

    response = requests.patch(student_db_url, json=data, headers=db_request_token())

    if is_response_valid(response, "Student API could not patch the data!"):
        updated_data = is_response_empty(
            response.json(), True, "Student API could not fetch the patched student"
        )
        logger.info("Successfully updated student record")
        return updated_data

    return None


async def create_student(student_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new student record."""
    logger.info(f"Creating student with data: {student_data}")

    response = requests.post(
        student_db_url, json=student_data, headers=db_request_token()
    )

    if is_response_valid(response, "Student API could not create the student!"):
        logger.info("Successfully created student")
        return response.json()

    return None
