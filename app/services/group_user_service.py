"""Group User service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException
from logger_config import get_logger
from routes import group_user_db_url
from helpers import db_request_token, is_response_valid
from settings import settings
from services.auth_group_service import get_auth_group_by_name
from services.batch_service import get_batch_by_id
from services.group_service import get_group_by_child_id_and_type
from mapping import authgroup_state_mapping
from services.school_service import get_school

logger = get_logger()


async def create_group_user(
    group_id: str, user_id: str, academic_year: str = None, start_date: str = None
) -> Optional[Dict[str, Any]]:
    """Create group user record."""
    data = {
        "group_id": group_id,
        "user_id": user_id,
        "academic_year": academic_year or settings.DEFAULT_ACADEMIC_YEAR,
    }

    if start_date:
        data["start_date"] = start_date

    logger.info(f"Creating group user record: {data}")

    response = requests.post(group_user_db_url, data=data, headers=db_request_token())

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


async def create_auth_group_user_record(data, auth_group_name):
    """Create auth group user record"""
    auth_group_data = get_auth_group_by_name(auth_group_name)
    if not auth_group_data or "id" not in auth_group_data:
        raise HTTPException(status_code=404, detail="Auth group not found")

    group_data = get_group_by_child_id_and_type(
        child_id=auth_group_data["id"], group_type="auth_group"
    )
    if not group_data or not isinstance(group_data, dict) or "id" not in group_data:
        raise HTTPException(status_code=404, detail="Auth group group not found")

    user_data = data.get("user", {})
    if not isinstance(user_data, dict) or "id" not in user_data:
        raise HTTPException(status_code=500, detail="Invalid user data")

    await create_group_user(
        group_id=group_data["id"],
        user_id=user_data["id"],
        academic_year=settings.DEFAULT_ACADEMIC_YEAR,
        start_date=datetime.now().strftime("%Y-%m-%d"),
    )


async def create_batch_user_record(data, batch_id):
    """Create batch user record"""
    batch_data = get_batch_by_id(batch_id)
    if not batch_data or "id" not in batch_data:
        raise HTTPException(status_code=404, detail="Batch not found")

    group_data = get_group_by_child_id_and_type(
        child_id=batch_data["id"], group_type="batch"
    )
    if not group_data or not isinstance(group_data, dict) or "id" not in group_data:
        raise HTTPException(status_code=404, detail="Batch group not found")

    user_data = data.get("user", {})
    if not isinstance(user_data, dict) or "id" not in user_data:
        raise HTTPException(status_code=500, detail="Invalid user data")

    await create_group_user(
        group_id=group_data["id"],
        user_id=user_data["id"],
        academic_year=settings.DEFAULT_ACADEMIC_YEAR,
        start_date=datetime.now().strftime("%Y-%m-%d"),
    )


async def create_school_user_record(
    data, school_name, district, auth_group_name=None, block_name=None
):
    """Create school user record"""
    state = (
        authgroup_state_mapping.get(auth_group_name, "") if auth_group_name else None
    )

    # Use the flexible get_school function to handle all parameters including block_name
    school_params = {"name": str(school_name), "district": str(district)}
    if state:
        school_params["state"] = state
    if block_name:
        school_params["block_name"] = str(block_name)

    school_data = get_school(**school_params)

    if not school_data or "id" not in school_data:
        raise HTTPException(status_code=404, detail="School not found")

    group_data = get_group_by_child_id_and_type(
        child_id=school_data["id"], group_type="school"
    )
    if not group_data or not isinstance(group_data, dict) or "id" not in group_data:
        raise HTTPException(status_code=404, detail="School group not found")

    user_data = data.get("user", {})
    if not isinstance(user_data, dict) or "id" not in user_data:
        raise HTTPException(status_code=500, detail="Invalid user data")

    await create_group_user(
        group_id=group_data["id"],
        user_id=user_data["id"],
        academic_year=settings.DEFAULT_ACADEMIC_YEAR,
        start_date=datetime.now().strftime("%Y-%m-%d"),
    )


async def create_grade_user_record(data):
    """Create grade user record"""
    grade_id = data.get("grade_id")
    if not grade_id:
        raise HTTPException(status_code=400, detail="Grade ID is required")

    group_data = get_group_by_child_id_and_type(child_id=grade_id, group_type="grade")
    if not group_data or not isinstance(group_data, dict) or "id" not in group_data:
        raise HTTPException(status_code=404, detail="Grade group not found")

    user_data = data.get("user", {})
    if not isinstance(user_data, dict) or "id" not in user_data:
        raise HTTPException(status_code=500, detail="Invalid user data")

    await create_group_user(
        group_id=group_data["id"],
        user_id=user_data["id"],
        academic_year=settings.DEFAULT_ACADEMIC_YEAR,
        start_date=datetime.now().strftime("%Y-%m-%d"),
    )
