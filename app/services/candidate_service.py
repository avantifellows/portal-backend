"""Candidate service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from logger_config import get_logger
from routes import candidate_db_url
from helpers import db_request_token, is_response_valid, safe_get_first_item
from mapping import CANDIDATE_QUERY_PARAMS
from services.subject_service import get_subject_by_name
from services.group_user_service import (
    create_auth_group_user_record,
    create_batch_user_record,
)
from helpers import validate_and_build_query_params, is_response_empty
from mapping import USER_QUERY_PARAMS
from fastapi import HTTPException

logger = get_logger()


def get_candidate_by_id(candidate_id: str) -> Optional[Dict[str, Any]]:
    """Get candidate by candidate_id."""
    return get_candidates(candidate_id=candidate_id)


def get_candidates(**params) -> Optional[Dict[str, Any]]:
    """Get candidates with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v for k, v in params.items() if v is not None and k in CANDIDATE_QUERY_PARAMS
    }

    logger.info(f"Fetching candidates with params: {query_params}")

    response = requests.get(
        candidate_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Candidate API could not fetch the data!"):
        candidate_data = safe_get_first_item(
            response.json(), "Candidate does not exist!"
        )
        logger.info("Successfully retrieved candidate data")
        return candidate_data

    return None


async def verify_candidate_by_id(candidate_id: str, **params) -> bool:
    """Verify candidate exists."""
    try:
        candidate_data = get_candidates(candidate_id=candidate_id, **params)
        return bool(candidate_data)
    except Exception as e:
        logger.error(f"Error verifying candidate {candidate_id}: {str(e)}")
        return False


async def create_candidate(request_or_data):
    """Create candidate with full business logic - moved from router."""
    try:
        # Handle both Request objects (from API calls) and direct data (from internal calls)
        if hasattr(request_or_data, "json"):
            data = await request_or_data.json()
        else:
            data = request_or_data

        logger.info(
            f"Creating candidate with auth_group: {data.get('auth_group', 'unknown')}"
        )

        query_params = validate_and_build_query_params(
            data["form_data"],
            CANDIDATE_QUERY_PARAMS + USER_QUERY_PARAMS + ["subject"],
        )

        # For HiringCandidates, use phone as candidate_id
        if data["auth_group"] == "HiringCandidates":
            phone = query_params.get("phone")
            if not phone:
                raise HTTPException(
                    status_code=400,
                    detail="Phone number is required for candidate registration",
                )

            query_params["candidate_id"] = phone
            candidate_id = phone

            # Check if candidate already exists
            candidate_already_exists = await verify_candidate_by_id(candidate_id)

            if candidate_already_exists:
                logger.info(f"Candidate already exists: {candidate_id}")
                return {"candidate_id": candidate_id, "already_exists": True}

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

        # Set user_type as candidate
        query_params["role"] = "candidate"

        # Create new candidate record
        response = requests.post(
            candidate_db_url, json=query_params, headers=db_request_token()
        )
        if not is_response_valid(response, "Candidate API could not post the data!"):
            raise HTTPException(
                status_code=500, detail="Failed to create candidate record"
            )

        new_candidate_data = is_response_empty(
            response.json(), True, "Candidate API could not fetch the created candidate"
        )

        # Create auth group user record (HiringCandidates)
        await create_auth_group_user_record(new_candidate_data, data["auth_group"])

        # Create batch user record (H-CN-25)
        if data["auth_group"] == "HiringCandidates":
            batch_id = "H-CN-25"
            await create_batch_user_record(new_candidate_data, batch_id)

        final_candidate_id = query_params.get("candidate_id", "unknown")
        logger.info(f"Successfully created candidate: {final_candidate_id}")
        return {"candidate_id": final_candidate_id, "already_exists": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_candidate: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating candidate")
