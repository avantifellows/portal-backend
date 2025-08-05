"""Teacher service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from logger_config import get_logger
from routes import teacher_db_url
from helpers import db_request_token, is_response_valid, safe_get_first_item
from mapping import TEACHER_QUERY_PARAMS

logger = get_logger()


def get_teacher_by_id(teacher_id: str) -> Optional[Dict[str, Any]]:
    """Get teacher by teacher_id."""
    return get_teachers(teacher_id=teacher_id)


def get_teachers(**params) -> Optional[Dict[str, Any]]:
    """Get teachers with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v for k, v in params.items() if v is not None and k in TEACHER_QUERY_PARAMS
    }

    logger.info(f"Fetching teachers with params: {query_params}")

    response = requests.get(
        teacher_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Teacher API could not fetch the data!"):
        teacher_data = safe_get_first_item(response.json(), "Teacher does not exist!")
        logger.info("Successfully retrieved teacher data")
        return teacher_data

    return None


async def verify_teacher_by_id(teacher_id: str, **params) -> bool:
    """Verify teacher exists."""
    try:
        teacher_data = get_teachers(teacher_id=teacher_id, **params)
        return bool(teacher_data)
    except Exception as e:
        logger.error(f"Error verifying teacher {teacher_id}: {str(e)}")
        return False


async def create_teacher(request_or_data):
    """Create teacher with full business logic - moved from router."""
    from services.subject_service import get_subject_by_name
    from services.group_user_service import (
        create_auth_group_user_record,
        create_batch_user_record,
        create_school_user_record,
    )
    from helpers import validate_and_build_query_params, is_response_empty
    from mapping import USER_QUERY_PARAMS, SCHOOL_QUERY_PARAMS
    from fastapi import HTTPException
    import requests

    try:
        # Handle both Request objects (from API calls) and direct data (from internal calls)
        if hasattr(request_or_data, "json"):
            data = await request_or_data.json()
        else:
            data = request_or_data

        logger.info(
            f"Creating teacher with auth_group: {data.get('auth_group', 'unknown')}"
        )

        query_params = validate_and_build_query_params(
            data["form_data"],
            TEACHER_QUERY_PARAMS
            + USER_QUERY_PARAMS
            + SCHOOL_QUERY_PARAMS
            + ["subject"],
        )

        # For PunjabTeachers, use phone as teacher_id
        if data["auth_group"] == "PunjabTeachers":
            phone = query_params.get("phone")
            if not phone:
                raise HTTPException(
                    status_code=400,
                    detail="Phone number is required for teacher registration",
                )

            query_params["teacher_id"] = phone
            teacher_id = phone

            # Check if teacher already exists
            teacher_already_exists = await verify_teacher_by_id(teacher_id)

            if teacher_already_exists:
                logger.info(f"Teacher already exists: {teacher_id}")
                return {"teacher_id": teacher_id, "already_exists": True}

            query_params["is_af_teacher"] = False  # PunjabTeachers are not AF teachers

        # Map subject name to subject_id like grade/grade_id in student.py
        if "subject" in query_params:
            try:
                subject_data = get_subject_by_name(query_params["subject"])
                if subject_data and "id" in subject_data:
                    query_params["subject_id"] = subject_data["id"]
                else:
                    logger.warning(
                        f"Subject not found for name: {query_params['subject']}"
                    )
                    # Fallback to subject name as subject_id
                    query_params["subject_id"] = query_params["subject"]
            except Exception as e:
                logger.error(f"Error fetching subject: {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Error processing subject information"
                )

        # Create new teacher record
        from routes import teacher_db_url

        response = requests.post(
            teacher_db_url, json=query_params, headers=db_request_token()
        )
        if not is_response_valid(response, "Teacher API could not post the data!"):
            raise HTTPException(
                status_code=500, detail="Failed to create teacher record"
            )

        new_teacher_data = is_response_empty(
            response.json(), True, "Teacher API could not fetch the created teacher"
        )

        # Create auth group user record (PunjabTeachers)
        await create_auth_group_user_record(new_teacher_data, data["auth_group"])

        # Create batch user record (PunjabTeachers_25_001)
        if data["auth_group"] == "PunjabTeachers":
            batch_id = "PunjabTeachers_25_001"
            await create_batch_user_record(new_teacher_data, batch_id)

        # Create school user record
        if "school_name" in query_params and "district" in query_params:
            school_name = query_params["school_name"]
            district = query_params["district"]
            block_name = query_params.get("block_name")
            await create_school_user_record(
                new_teacher_data, school_name, district, data["auth_group"], block_name
            )

        final_teacher_id = query_params.get("teacher_id", "unknown")
        logger.info(f"Successfully created teacher: {final_teacher_id}")
        return {"teacher_id": final_teacher_id, "already_exists": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_teacher: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating teacher")
