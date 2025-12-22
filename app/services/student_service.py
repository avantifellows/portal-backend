"""Student service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from logger_config import get_logger
from routes import student_db_url
from helpers import (
    db_request_token,
    is_response_valid,
    is_response_empty,
    safe_get_first_item,
)
from mapping import (
    STUDENT_QUERY_PARAMS,
    USER_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
)
from services.exam_service import get_exam_by_name
from services.school_service import get_school
from services.group_service import get_group_by_child_id_and_type
from services.group_user_service import (
    get_group_user,
    create_auth_group_user_record,
    create_batch_user_record,
    create_school_user_record,
    create_grade_user_record,
)
from services.grade_service import get_grade_by_number
from services.user_service import get_user_by_email_and_phone
from auth_group_classes import EnableStudents
from mapping import SCHOOL_QUERY_PARAMS, authgroup_state_mapping
from helpers import validate_and_build_query_params
from fastapi import HTTPException

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

    try:
        # Extract ID for URL path and remove from data payload
        student_record_id = data.pop("id", None)
        if not student_record_id:
            logger.error("No student ID found in data for PATCH request")
            return None

        # Build URL with ID in path: /api/student/86081
        patch_url = f"{student_db_url}/{student_record_id}"

        response = requests.patch(patch_url, json=data, headers=db_request_token())

    except requests.exceptions.RequestException as e:
        logger.error(f"PATCH Request failed with exception: {e}")
        raise

    if is_response_valid(response, "Student API could not patch the data!"):
        updated_data = is_response_empty(
            response.json(), True, "Student API could not fetch the patched student"
        )
        logger.info("Successfully updated student record")
        return updated_data

    return None


def process_exams(student_exam_texts: list) -> list:
    """Process exam texts and return exam IDs."""
    student_exam_ids = []
    try:
        for exam_name in student_exam_texts:
            exam_data = get_exam_by_name(exam_name)
            if exam_data and "id" in exam_data:
                student_exam_ids.append(exam_data["id"])
            else:
                logger.warning(f"Exam not found for name: {exam_name}")
    except Exception as e:
        logger.error(f"Error processing exams: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing exam data")

    return student_exam_ids


def validate_school_exists(
    school_name: str,
    district: str,
    auth_group_name: str,
    block_name: Optional[str] = None,
) -> tuple[bool, str]:
    """Validate that school exists before creating student - fail fast."""
    try:
        if not school_name or not district:
            logger.warning(
                f"Missing school data - name: {school_name}, district: {district}"
            )
            return False, "School name and district are required"

        state = authgroup_state_mapping.get(auth_group_name, "")

        logger.info(
            f"Validating school: {school_name}, {district}, {state}, block: {block_name}"
        )

        school_params = {"name": str(school_name), "district": str(district)}
        if state:
            school_params["state"] = state
        if block_name:
            school_params["block_name"] = str(block_name)

        school_data = get_school(**school_params)

        if not school_data or "id" not in school_data:
            logger.warning(
                f"School not found during validation: {school_name}, {district}"
            )
            return False, f"School '{school_name}' not found in district '{district}'"

        group_data = get_group_by_child_id_and_type(
            child_id=school_data["id"], group_type="school"
        )

        if not group_data or not isinstance(group_data, dict) or "id" not in group_data:
            logger.warning(
                f"School group not found during validation for school: {school_data['id']}"
            )
            return (
                False,
                f"School '{school_name}' exists but is not properly configured (missing group)",
            )

        logger.info(f"School validation successful: {school_name}")
        return True, "School validation successful"

    except Exception as e:
        logger.error(f"Error validating school: {str(e)}")
        return False, f"Error validating school: {str(e)}"


def build_student_and_user_data(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build student and user data with proper validation."""
    data = {}
    try:
        for key in student_data.keys():
            if key in STUDENT_QUERY_PARAMS + USER_QUERY_PARAMS:
                if key == "physically_handicapped":
                    data[key] = "true" if student_data[key] == "Yes" else "false"
                elif key == "has_category_certificate":
                    data[key] = "true" if student_data[key] == "Yes" else "false"
                elif (
                    key == "category"
                    and student_data.get("physically_handicapped") == "Yes"
                ):
                    data[key] = f"PWD-{student_data[key].split('-')[-1]}"
                elif key == "planned_competitive_exams":
                    data[key] = process_exams(student_data[key])
                else:
                    data[key] = student_data[key]
    except Exception as e:
        logger.error(f"Error building student and user data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing student data")

    return data


def create_new_student_record(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create new student record with proper error handling."""
    try:
        logger.info("Creating new student record")

        response = requests.post(student_db_url, json=data, headers=db_request_token())

        if is_response_valid(response, "Student API could not post the data!"):
            try:
                response_data = response.json()
                created_student_data = is_response_empty(
                    response_data,
                    True,
                    "Student API could not fetch the created student",
                )

                logger.info("Successfully created student record")
                return created_student_data
            except ValueError as json_error:
                logger.error(f"Failed to parse JSON response: {json_error}")
                logger.error(f"Response content: {response.text}")
                raise HTTPException(
                    status_code=500, detail="Invalid JSON response from student API"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating student record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating student record")

    return None


def check_if_email_or_phone_is_part_of_request(query_params: Dict[str, Any]) -> None:
    """Check if email or phone is part of request."""
    if (
        "email" not in query_params
        or query_params["email"] == ""
        or query_params["email"] is None
    ) and (
        "phone" not in query_params
        or query_params["phone"] == ""
        or query_params["phone"] is None
    ):
        raise HTTPException(
            status_code=400, detail="Email/Phone is not part of the request data"
        )


def check_if_student_id_is_part_of_request(query_params: Dict[str, Any]) -> None:
    """Check if student_id is part of request."""
    if (
        "student_id" not in query_params
        or query_params["student_id"] == ""
        or query_params["student_id"] is None
    ):
        raise HTTPException(
            status_code=400, detail="Student ID is not part of the request data"
        )


async def verify_student_comprehensive(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensive student verification with multiple fallback methods.

    Returns a payload containing verification status and core identifiers so that
    clients don't have to re-fetch the student record after validation.
    """
    student_id = query_params.get("student_id")
    phone = query_params.get("phone")
    auth_group_id = query_params.get("auth_group_id")

    if not student_id and not phone:
        raise HTTPException(
            status_code=400, detail="Either student_id or phone is required"
        )

    if not student_id and phone:
        student_id = phone

    logger.info(f"Verifying student: {student_id} with params: {query_params}")

    invalid_response = {"is_valid": False}

    is_enable_students = auth_group_id == "3"  # EnableStudents auth_group_id
    if is_enable_students:
        logger.info(
            "Detected EnableStudents auth group - will try apaar_id fallback if needed"
        )

    student_record = None

    # Try student_id first
    response = requests.get(
        student_db_url,
        params={"student_id": student_id},
        headers=db_request_token(),
    )

    if is_response_valid(response):
        student_data = is_response_empty(response.json(), False)
        if student_data:
            student_record = (
                safe_get_first_item(student_data)
                if isinstance(student_data, list)
                else student_data
            )

    # For EnableStudents: if no student found with student_id, try apaar_id
    found_via_apaar_id = False
    if not student_record and is_enable_students:
        logger.info(f"EnableStudents: Trying apaar_id for: {student_id}")

        response = requests.get(
            student_db_url,
            params={"apaar_id": student_id},
            headers=db_request_token(),
        )

        if is_response_valid(response):
            student_data = is_response_empty(response.json(), False)
            if student_data:
                student_record = (
                    safe_get_first_item(student_data)
                    if isinstance(student_data, list)
                    else student_data
                )
                found_via_apaar_id = True

    # If still no student found and we have phone, try searching by phone
    found_via_phone = False
    if not student_record and phone and phone != student_id:
        logger.info(f"Trying phone search for: {phone}")

        response = requests.get(
            student_db_url,
            params={"phone": phone},
            headers=db_request_token(),
        )

        if is_response_valid(response):
            student_data = is_response_empty(response.json(), False)
            if student_data:
                student_record = (
                    safe_get_first_item(student_data)
                    if isinstance(student_data, list)
                    else student_data
                )
                found_via_phone = True

    if not student_record:
        logger.warning(f"No student found for: {student_id}")
        return invalid_response

    # Verify all query parameters
    for key, value in query_params.items():
        if key in USER_QUERY_PARAMS:
            user_data = student_record.get("user", {})
            if not isinstance(user_data, dict):
                logger.warning(f"Invalid user data structure for student: {student_id}")
                return invalid_response
            if user_data.get(key) != value:
                logger.info(f"User verification failed for key: {key}")
                return invalid_response

        elif key in STUDENT_QUERY_PARAMS:
            # Skip student_id verification if we found the student via apaar_id or phone
            if key == "student_id" and (found_via_apaar_id or found_via_phone):
                logger.info(
                    "Skipping student_id verification - found via alternative method"
                )
                continue
            if student_record.get(key) != value:
                logger.info(f"Student verification failed for key: {key}")
                return invalid_response

        elif key == "auth_group_id":
            # Verify user belongs to the auth group
            group_response = get_group_by_child_id_and_type(
                child_id=value, group_type="auth_group"
            )

            if not (
                group_response
                and isinstance(group_response, dict)
                and "id" in group_response
            ):
                logger.warning(f"Group not found for auth_group_id: {value}")
                return invalid_response

            group_record = group_response
            if not (isinstance(group_record, dict) and "id" in group_record):
                logger.warning("Invalid group record structure")
                return invalid_response

            user_data = student_record.get("user", {})
            if not (isinstance(user_data, dict) and "id" in user_data):
                logger.warning("Invalid user data in student record")
                return invalid_response

            group_user_response = get_group_user(
                group_id=group_record["id"], user_id=user_data["id"]
            )
            if not group_user_response or group_user_response == []:
                logger.info("User not found in auth group")
                return invalid_response

    identifiers = {
        "student_id": student_record.get("student_id"),
        "apaar_id": student_record.get("apaar_id"),
        "user_id": None,
    }

    for key, value in list(identifiers.items()):
        if value is not None:
            identifiers[key] = str(value)

    user_data = student_record.get("user", {})
    if isinstance(user_data, dict):
        user_id = user_data.get("id")
        if user_id is not None:
            identifiers["user_id"] = str(user_id)

    logger.info(f"Student verification successful for: {student_id}")
    return {"is_valid": True, **identifiers}


async def complete_profile_details_service(
    data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Complete profile details - business logic."""
    try:
        logger.info(
            f"Completing profile details for student: {data.get('student_id', 'unknown')}"
        )

        student_data = build_student_and_user_data(data)

        student_response = get_student_by_id(data["student_id"])

        if (
            not student_response
            or not isinstance(student_response, list)
            or len(student_response) == 0
        ):
            logger.error(f"Student not found for ID: {data.get('student_id')}")
            raise HTTPException(status_code=404, detail="Student not found")

        # Safe access to first student
        first_student = student_response[0]
        if not isinstance(first_student, dict) or "id" not in first_student:
            logger.error(f"Invalid student data structure: {first_student}")
            raise HTTPException(status_code=500, detail="Invalid student data")

        student_data["id"] = first_student["id"]
        # Remove student_id from patch data as it's an identifier, not an updatable field
        if "student_id" in student_data:
            del student_data["student_id"]
        result = await update_student_data(student_data)

        logger.info("Successfully completed profile details")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing profile details: {str(e)}")
        raise HTTPException(status_code=500, detail="Error completing profile details")


async def create_student(request_or_data):
    """Create student with full business logic - moved from router."""

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
                "BiharStudents",
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


async def patch_student_service(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update student record - service layer."""
    try:
        logger.info("Updating student record")

        response = requests.patch(student_db_url, json=data, headers=db_request_token())

        if is_response_valid(response, "Student API could not patch the data!"):
            updated_data = is_response_empty(
                response.json(), True, "Student API could not fetch the patched student"
            )
            logger.info("Successfully updated student record")
            return updated_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating student: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating student")

    return None
