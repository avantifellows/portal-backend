"""Student service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from logger_config import get_logger
from routes import student_db_url
from helpers import db_request_token, is_response_valid, is_response_empty
from mapping import (
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


async def create_student(request_or_data):
    """Create student with full business logic - moved from router."""
    from services.exam_service import get_exam_by_name
    from services.school_service import get_school
    from services.group_service import get_group_by_child_id_and_type
    from services.group_user_service import (
        create_auth_group_user_record,
        create_batch_user_record,
        create_school_user_record,
        create_grade_user_record,
    )
    from services.grade_service import get_grade_by_number
    from services.user_service import get_user_by_email_and_phone
    from auth_group_classes import EnableStudents
    from mapping import SCHOOL_QUERY_PARAMS, authgroup_state_mapping
    from helpers import validate_and_build_query_params, safe_get_first_item
    from fastapi import HTTPException

    try:
        # Handle both Request objects (from API calls) and direct data (from internal calls)
        if hasattr(request_or_data, "json"):
            data = await request_or_data.json()
        else:
            data = request_or_data

        logger.info(
            f"Creating student with auth_group: {data.get('auth_group', 'unknown')}"
        )

        query_params = validate_and_build_query_params(
            data["form_data"],
            STUDENT_QUERY_PARAMS
            + USER_QUERY_PARAMS
            + ENROLLMENT_RECORD_PARAMS
            + SCHOOL_QUERY_PARAMS
            + ["id_generation", "region", "batch_registration"],
        )

        # School validation
        if "school_name" in query_params:
            school_name = query_params["school_name"]
            district = query_params.get("district")
            if not district:
                raise HTTPException(
                    status_code=400,
                    detail="District is required when school name is provided",
                )

            block_name = query_params.get("block_name")
            state = authgroup_state_mapping.get(data["auth_group"], "")

            school_params = {"name": str(school_name), "district": str(district)}
            if state:
                school_params["state"] = state
            if block_name:
                school_params["block_name"] = str(block_name)

            school_data = get_school(**school_params)
            if not school_data or "id" not in school_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"School '{school_name}' not found in district '{district}'",
                )

        # ID generation logic
        if not data["id_generation"]:
            student_id = query_params.get("student_id")
            if not student_id:
                raise HTTPException(status_code=400, detail="Student ID is required")

            if await verify_student_by_id(student_id):
                return {"student_id": student_id, "already_exists": True}
        else:
            if data["auth_group"] == "EnableStudents":
                student_id = EnableStudents(query_params).get_student_id()
                query_params["student_id"] = student_id
                if student_id == "":
                    return {
                        "student_id": query_params["student_id"],
                        "already_exists": True,
                    }
            elif data["auth_group"] in [
                "FeedingIndiaStudents",
                "UttarakhandStudents",
                "HimachalStudents",
                "AllIndiaStudents",
                "ChhattisgarhStudents",
                "MaharashtraStudents",
            ]:
                phone = query_params.get("phone")
                if not phone:
                    raise HTTPException(
                        status_code=400,
                        detail="Phone number is required for this auth group",
                    )
                query_params["student_id"] = phone
                if await verify_student_by_id(phone):
                    return {"student_id": phone, "already_exists": True}
            else:
                if not (query_params.get("email") or query_params.get("phone")):
                    raise HTTPException(
                        status_code=400, detail="Email/Phone is required"
                    )
                if get_user_by_email_and_phone(
                    email=query_params.get("email"), phone=query_params.get("phone")
                ):
                    return {
                        "student_id": query_params.get("student_id", "unknown"),
                        "already_exists": True,
                    }

        # Process grade
        if "grade" in query_params:
            try:
                student_grade_data = get_grade_by_number(int(query_params["grade"]))
                if student_grade_data and "id" in student_grade_data:
                    query_params["grade_id"] = student_grade_data["id"]
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error processing grade information {e}"
                )

        # Process exams
        if "planned_competitive_exams" in query_params:
            exam_ids = []
            for exam_name in query_params["planned_competitive_exams"]:
                exam_data = get_exam_by_name(exam_name)
                if exam_data and "id" in exam_data:
                    exam_ids.append(exam_data["id"])
            query_params["planned_competitive_exams"] = exam_ids

        # Process category for PWD
        if (
            "category" in query_params
            and query_params.get("physically_handicapped") == "Yes"
        ):
            query_params["category"] = f"PWD-{query_params['category'].split('-')[-1]}"

        # Process boolean fields
        if "physically_handicapped" in query_params:
            query_params["physically_handicapped"] = (
                "true" if query_params["physically_handicapped"] == "Yes" else "false"
            )

        # Create student record
        response = requests.post(
            student_db_url, json=query_params, headers=db_request_token()
        )
        if not is_response_valid(response, "Student API could not post the data!"):
            raise HTTPException(
                status_code=500, detail="Failed to create student record"
            )

        new_student_data = is_response_empty(
            response.json(), True, "Student API could not fetch the created student"
        )

        # Create related records
        await create_auth_group_user_record(new_student_data, data["auth_group"])

        if data["auth_group"] == "AllIndiaStudents":
            grade_value = query_params.get("grade", "unknown")
            batch_id = f"AllIndiaStudents_{grade_value}_24_A001"
            await create_batch_user_record(new_student_data, batch_id)

        if (
            data["auth_group"]
            in [
                "HimachalStudents",
                "DelhiStudents",
                "UttarakhandStudents",
                "PunjabStudents",
            ]
            and "grade" in query_params
            and query_params.get("batch_registration")
        ):
            grade_value = query_params["grade"]
            if data["auth_group"] == "HimachalStudents":
                batch_id = f"HP-{grade_value}-Selection-25"
            elif data["auth_group"] == "UttarakhandStudents":
                batch_id = f"UK-{grade_value}-Selection-25"
            elif data["auth_group"] == "DelhiStudents":
                batch_id = f"DL-{grade_value}-Selection-25"
            elif data["auth_group"] == "PunjabStudents":
                batch_id = f"PB-{grade_value}-Selection-25"
            await create_batch_user_record(new_student_data, batch_id)

        if "grade_id" in new_student_data:
            await create_grade_user_record(new_student_data)

        if "school_name" in query_params:
            await create_school_user_record(
                new_student_data,
                query_params["school_name"],
                query_params.get("district"),
                data["auth_group"],
                query_params.get("block_name"),
            )

        final_student_id = query_params.get("student_id", "unknown")
        logger.info(f"Successfully created student: {final_student_id}")
        return {"student_id": final_student_id, "already_exists": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_student: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating student")
