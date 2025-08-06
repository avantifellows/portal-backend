from fastapi import APIRouter, HTTPException, Request
import requests
from services.exam_service import get_exam_by_name
from services.school_service import get_school
from services.group_service import get_group_by_child_id_and_type
from services.group_user_service import (
    get_group_user,
)
from services.student_service import (
    get_student_by_id,
    update_student_data,
)
from routes import student_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
    safe_get_first_item,
)
from logger_config import get_logger
from mapping import (
    USER_QUERY_PARAMS,
    STUDENT_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
    authgroup_state_mapping,
)
from services.student_service import create_student as create_student_service

router = APIRouter(prefix="/student", tags=["Student"])
logger = get_logger()


def process_exams(student_exam_texts):
    """Process exam texts and return exam IDs"""
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


def validate_school_exists(school_name, district, auth_group_name, block_name=None):
    """Validate that school exists before creating student - fail fast"""
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

        # Also validate that the school has a group
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


def build_student_and_user_data(student_data):
    """Build student and user data with proper validation"""
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


def create_new_student_record(data):
    """Create new student record with proper error handling"""
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


def check_if_email_or_phone_is_part_of_request(query_params):
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
    return


def check_if_student_id_is_part_of_request(query_params):
    if (
        "student_id" not in query_params
        or query_params["student_id"] == ""
        or query_params["student_id"] is None
    ):
        raise HTTPException(
            status_code=400, detail="Student ID is not part of the request data"
        )
    return


@router.get("/")
def get_students(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        STUDENT_QUERY_PARAMS + USER_QUERY_PARAMS + ENROLLMENT_RECORD_PARAMS,
    )

    logger.info(f"Fetching students with params: {query_params}")

    response = requests.get(
        student_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Student API could not fetch the student!"):
        students_data = is_response_empty(
            response.json(), False, "Student does not exist"
        )
        logger.info(
            f"Successfully retrieved {len(students_data) if isinstance(students_data, list) else 1} student(s)"
        )
        return students_data


@router.get("/verify")
async def verify_student(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        STUDENT_QUERY_PARAMS + USER_QUERY_PARAMS + ["auth_group_id"],
    )

    # Check if we have either student_id or phone for identification
    student_id = query_params.get("student_id")
    phone = query_params.get("phone")

    if not student_id and not phone:
        raise HTTPException(
            status_code=400, detail="Either student_id or phone is required"
        )

    # Use phone as student_id if no student_id provided
    if not student_id and phone:
        student_id = phone

    logger.info(f"Verifying student: {student_id} with params: {query_params}")

    # Check if this is EnableStudents auth group (temporary hardcoded check)
    # TODO: Remove check for EnableStudents auth group when apaar_id merges with student_id
    auth_group_id = query_params.get("auth_group_id")
    is_enable_students = auth_group_id == "3"  # EnableStudents auth_group_id
    if is_enable_students:
        logger.info(
            "Detected EnableStudents auth group - will try apaar_id fallback if needed"
        )

    # Try student_id first
    student_record = None
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

    # Now verify the student record against all query params
    if not student_record:
        logger.warning(f"No student found for: {student_id}")
        return False

    # Verify all query parameters
    for key, value in query_params.items():
        if key in USER_QUERY_PARAMS:
            user_data = student_record.get("user", {})
            if not isinstance(user_data, dict):
                logger.warning(f"Invalid user data structure for student: {student_id}")
                return False
            if user_data.get(key) != value:
                logger.info(f"User verification failed for key: {key}")
                return False

        elif key in STUDENT_QUERY_PARAMS:
            # Skip student_id verification if we found the student via apaar_id or phone
            if key == "student_id" and (found_via_apaar_id or found_via_phone):
                logger.info(
                    "Skipping student_id verification - found via alternative method"
                )
                continue
            if student_record.get(key) != value:
                logger.info(f"Student verification failed for key: {key}")
                return False

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
                return False

            group_record = group_response
            if not (isinstance(group_record, dict) and "id" in group_record):
                logger.warning("Invalid group record structure")
                return False

            user_data = student_record.get("user", {})
            if not (isinstance(user_data, dict) and "id" in user_data):
                logger.warning("Invalid user data in student record")
                return False

            group_user_response = get_group_user(
                group_id=group_record["id"], user_id=user_data["id"]
            )
            if not group_user_response or group_user_response == []:
                logger.info("User not found in auth group")
                return False

    logger.info(f"Student verification successful for: {student_id}")
    return True


@router.post("/")
async def create_student(request: Request):
    """Thin router layer - delegates to service."""
    return await create_student_service(request)


@router.patch("/")
async def update_student(request: Request):
    try:
        data = await request.json()
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


@router.post("/complete-profile-details")
async def complete_profile_details(request: Request):
    try:
        data = await request.json()
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
