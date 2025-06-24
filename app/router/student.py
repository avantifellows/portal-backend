from fastapi import APIRouter, HTTPException, Request
import requests
from router import (
    group,
    auth_group,
    batch,
    group_user,
    user,
    school,
    grade,
    exam,
)
from auth_group_classes import EnableStudents
from request import build_request
from routes import student_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
    safe_get_first_item,
)
from logger_config import get_logger
from datetime import datetime
from mapping import (
    USER_QUERY_PARAMS,
    STUDENT_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
    SCHOOL_QUERY_PARAMS,
    authgroup_state_mapping,
)

router = APIRouter(prefix="/student", tags=["Student"])
logger = get_logger()


def process_exams(student_exam_texts):
    """Process exam texts and return exam IDs"""
    student_exam_ids = []
    try:
        for exam_name in student_exam_texts:
            exam_data = exam.get_exam(build_request(query_params={"name": exam_name}))
            if exam_data and "id" in exam_data:
                student_exam_ids.append(exam_data["id"])
            else:
                logger.warning(f"Exam not found for name: {exam_name}")
    except Exception as e:
        logger.error(f"Error processing exams: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing exam data")

    return student_exam_ids


def validate_school_exists(school_name, district, auth_group_name):
    """Validate that school exists before creating student - fail fast"""
    try:
        if not school_name or not district:
            logger.warning(
                f"Missing school data - name: {school_name}, district: {district}"
            )
            return False, "School name and district are required"

        state = authgroup_state_mapping.get(auth_group_name, "")

        logger.info(f"Validating school: {school_name}, {district}, {state}")

        if state:
            school_data = school.get_school(
                build_request(
                    query_params={
                        "name": str(school_name),
                        "district": str(district),
                        "state": state,
                    }
                )
            )
        else:
            school_data = school.get_school(
                build_request(
                    query_params={"name": str(school_name), "district": str(district)}
                )
            )

        if not school_data or "id" not in school_data:
            logger.warning(
                f"School not found during validation: {school_name}, {district}"
            )
            return False, f"School '{school_name}' not found in district '{district}'"

        # Also validate that the school has a group
        group_data = group.get_group(
            build_request(
                query_params={"child_id": school_data["id"], "type": "school"}
            )
        )

        if not group_data or not isinstance(group_data, list) or len(group_data) == 0:
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
                elif key == "planned_competitive_exams":
                    data[key] = process_exams(student_data[key])
                else:
                    data[key] = student_data[key]
    except Exception as e:
        logger.error(f"Error building student and user data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing student data")

    return data


async def create_school_user_record(data, school_name, district, auth_group_name):
    """Create school user record with proper error handling"""
    try:
        state = authgroup_state_mapping.get(auth_group_name, "")

        logger.info(
            f"Creating school user record for {school_name}, {district}, {state}"
        )

        if state:
            school_data = school.get_school(
                build_request(
                    query_params={
                        "name": str(school_name),
                        "district": str(district),
                        "state": state,
                    }
                )
            )
        else:
            school_data = school.get_school(
                build_request(
                    query_params={"name": str(school_name), "district": str(district)}
                )
            )

        if not school_data or "id" not in school_data:
            logger.error(f"School not found: {school_name}, {district}")
            raise HTTPException(status_code=404, detail="School not found")

        group_data = group.get_group(
            build_request(
                query_params={"child_id": school_data["id"], "type": "school"}
            )
        )

        if not group_data or not isinstance(group_data, list) or len(group_data) == 0:
            logger.error(f"Group not found for school: {school_data['id']}")
            raise HTTPException(status_code=404, detail="School group not found")

        # Safe access to first group
        first_group = group_data[0]
        if not isinstance(first_group, dict) or "id" not in first_group:
            logger.error(f"Invalid group data structure: {first_group}")
            raise HTTPException(status_code=500, detail="Invalid group data")

        # Safe access to user data
        user_data = data.get("user", {})
        if not isinstance(user_data, dict) or "id" not in user_data:
            logger.error(f"Invalid user data structure: {user_data}")
            raise HTTPException(status_code=500, detail="Invalid user data")

        await group_user.create_group_user(
            build_request(
                method="POST",
                body={
                    "group_id": first_group["id"],
                    "user_id": user_data["id"],
                    "academic_year": "2025-2026",  # hardcoding; will figure better sol later
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                },
            )
        )

        logger.info("Successfully created school user record")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating school user record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating school user record")


async def create_batch_user_record(data, batch_id):
    """Create batch user record with proper error handling"""
    try:
        logger.info(f"Creating batch user record for batch_id: {batch_id}")

        batch_data = batch.get_batch(build_request(query_params={"batch_id": batch_id}))

        if not batch_data or "id" not in batch_data:
            logger.error(f"Batch not found: {batch_id}")
            raise HTTPException(status_code=404, detail="Batch not found")

        group_data = group.get_group(
            build_request(query_params={"child_id": batch_data["id"], "type": "batch"})
        )

        if not group_data or not isinstance(group_data, list) or len(group_data) == 0:
            logger.error(f"Group not found for batch: {batch_data['id']}")
            raise HTTPException(status_code=404, detail="Batch group not found")

        # Safe access to first group
        first_group = group_data[0]
        if not isinstance(first_group, dict) or "id" not in first_group:
            logger.error(f"Invalid group data structure: {first_group}")
            raise HTTPException(status_code=500, detail="Invalid group data")

        # Safe access to user data
        user_data = data.get("user", {})
        if not isinstance(user_data, dict) or "id" not in user_data:
            logger.error(f"Invalid user data structure: {user_data}")
            raise HTTPException(status_code=500, detail="Invalid user data")

        await group_user.create_group_user(
            build_request(
                method="POST",
                body={
                    "group_id": first_group["id"],
                    "user_id": user_data["id"],
                    "academic_year": "2025-2026",  # hardcoding; will figure better sol later
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                },
            )
        )

        logger.info("Successfully created batch user record")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating batch user record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating batch user record")


async def create_grade_user_record(data):
    """Create grade user record with proper error handling"""
    try:
        grade_id = data.get("grade_id")
        if not grade_id:
            logger.error("No grade_id found in data")
            raise HTTPException(status_code=400, detail="Grade ID is required")

        logger.info(f"Creating grade user record for grade_id: {grade_id}")

        group_data = group.get_group(
            build_request(query_params={"child_id": grade_id, "type": "grade"})
        )

        if not group_data or not isinstance(group_data, list) or len(group_data) == 0:
            logger.error(f"Group not found for grade: {grade_id}")
            raise HTTPException(status_code=404, detail="Grade group not found")

        # Safe access to first group
        first_group = group_data[0]
        if not isinstance(first_group, dict) or "id" not in first_group:
            logger.error(f"Invalid group data structure: {first_group}")
            raise HTTPException(status_code=500, detail="Invalid group data")

        # Safe access to user data
        user_data = data.get("user", {})
        if not isinstance(user_data, dict) or "id" not in user_data:
            logger.error(f"Invalid user data structure: {user_data}")
            raise HTTPException(status_code=500, detail="Invalid user data")

        await group_user.create_group_user(
            build_request(
                method="POST",
                body={
                    "group_id": first_group["id"],
                    "user_id": user_data["id"],
                    "academic_year": "2025-2026",  # hardcoding; will figure better sol later
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                },
            )
        )

        logger.info("Successfully created grade user record")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating grade user record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating grade user record")


async def create_auth_group_user_record(data, auth_group_name):
    """Create auth group user record with proper error handling"""
    try:
        logger.info(f"Creating auth group user record for: {auth_group_name}")

        auth_group_data = auth_group.get_auth_group(
            build_request(query_params={"name": auth_group_name})
        )

        if not auth_group_data or "id" not in auth_group_data:
            logger.error(f"Auth group not found: {auth_group_name}")
            raise HTTPException(status_code=404, detail="Auth group not found")

        group_data = group.get_group(
            build_request(
                query_params={"child_id": auth_group_data["id"], "type": "auth_group"}
            )
        )

        if not group_data or not isinstance(group_data, list) or len(group_data) == 0:
            logger.error(f"Group not found for auth group: {auth_group_data['id']}")
            raise HTTPException(status_code=404, detail="Auth group group not found")

        # Safe access to first group
        first_group = group_data[0]
        if not isinstance(first_group, dict) or "id" not in first_group:
            logger.error(f"Invalid group data structure: {first_group}")
            raise HTTPException(status_code=500, detail="Invalid group data")

        # Safe access to user data
        user_data = data.get("user", {})
        if not isinstance(user_data, dict) or "id" not in user_data:
            logger.error(f"Invalid user data structure: {user_data}")
            raise HTTPException(status_code=500, detail="Invalid user data")

        await group_user.create_group_user(
            build_request(
                method="POST",
                body={
                    "group_id": first_group["id"],
                    "user_id": user_data["id"],
                    "academic_year": "2025-2026",  # hardcoding; will figure better sol later
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                },
            )
        )

        logger.info("Successfully created auth group user record")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating auth group user record: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error creating auth group user record"
        )


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
async def verify_student(request: Request, student_id: str):
    query_params = validate_and_build_query_params(
        request.query_params,
        STUDENT_QUERY_PARAMS + USER_QUERY_PARAMS + ["auth_group_id"],
    )

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
            if student_record.get(key) != value:
                logger.info(f"Student verification failed for key: {key}")
                return False

        elif key == "auth_group_id":
            # Verify user belongs to the auth group
            group_response = group.get_group(
                build_request(
                    query_params={
                        "child_id": value,
                        "type": "auth_group",
                    }
                )
            )

            if not (
                group_response
                and isinstance(group_response, list)
                and len(group_response) > 0
            ):
                logger.warning(f"Group not found for auth_group_id: {value}")
                return False

            group_record = group_response[0]
            if not (isinstance(group_record, dict) and "id" in group_record):
                logger.warning("Invalid group record structure")
                return False

            user_data = student_record.get("user", {})
            if not (isinstance(user_data, dict) and "id" in user_data):
                logger.warning("Invalid user data in student record")
                return False

            group_user_response = group_user.get_group_user(
                build_request(
                    query_params={
                        "group_id": group_record["id"],
                        "user_id": user_data["id"],
                    }
                )
            )
            if not group_user_response or group_user_response == []:
                logger.info("User not found in auth group")
                return False

    logger.info(f"Student verification successful for: {student_id}")
    return True


@router.post("/")
async def create_student(request_or_data):
    try:
        # Handle both Request objects (from API calls) and direct data (from internal calls)
        if hasattr(request_or_data, "json"):
            # It's a Request object
            data = await request_or_data.json()
        else:
            # It's direct data
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
            + ["id_generation", "region", "batch_registration", "block_name"],
        )

        # Early validation: Check school exists if provided - FAIL FAST
        if "school_name" in query_params:
            school_name = query_params["school_name"]
            district = query_params.get("district")

            if not district:
                logger.error(f"School name provided but no district: {school_name}")
                raise HTTPException(
                    status_code=400,
                    detail="District is required when school name is provided",
                )

            school_valid, school_message = validate_school_exists(
                school_name, district, data["auth_group"]
            )

            if not school_valid:
                logger.error(f"School validation failed: {school_message}")
                raise HTTPException(
                    status_code=400,
                    detail=f"School validation failed: {school_message}",
                )

        if not data["id_generation"]:
            student_id = query_params.get("student_id")
            check_if_student_id_is_part_of_request(query_params)

            does_student_already_exist = await verify_student(
                build_request(), student_id
            )

            if does_student_already_exist:
                logger.info(f"Student already exists: {student_id}")
                return {"student_id": student_id, "already_exists": True}

        else:
            if data["auth_group"] == "EnableStudents":
                student_id = EnableStudents(query_params).get_student_id()
                query_params["student_id"] = student_id

                if student_id == "":
                    logger.info(
                        f"Student already exists (EnableStudents): {student_id}"
                    )
                    return {
                        "student_id": query_params["student_id"],
                        "already_exists": True,
                    }

            elif (
                data["auth_group"] == "FeedingIndiaStudents"
                or data["auth_group"] == "UttarakhandStudents"
                or data["auth_group"] == "HimachalStudents"
                or data["auth_group"] == "AllIndiaStudents"
                or data["auth_group"] == "ChhattisgarhStudents"
            ):
                # Use phone number as student ID
                phone = query_params.get("phone")
                if not phone:
                    raise HTTPException(
                        status_code=400,
                        detail="Phone number is required for this auth group",
                    )

                query_params["student_id"] = phone
                student_id = phone

                student_id_already_exists = await verify_student(
                    build_request(), student_id=student_id
                )

                if student_id_already_exists:
                    logger.info(f"Student already exists (phone-based): {student_id}")
                    return {
                        "student_id": student_id,
                        "already_exists": True,
                    }
            else:
                check_if_email_or_phone_is_part_of_request(query_params)

                user_already_exists = user.get_users(
                    build_request(
                        query_params={
                            "email": query_params.get("email"),
                            "phone": query_params.get("phone"),
                        }
                    )
                )
                if user_already_exists:
                    logger.info("User already exists with email/phone")
                    return {
                        "student_id": query_params.get("student_id", "unknown"),
                        "already_exists": True,
                    }

        if "grade" in query_params:
            try:
                student_grade_data = grade.get_grade(
                    build_request(query_params={"number": int(query_params["grade"])})
                )
                if student_grade_data and "id" in student_grade_data:
                    query_params["grade_id"] = student_grade_data["id"]
                else:
                    logger.warning(
                        f"Grade not found for number: {query_params['grade']}"
                    )
            except Exception as e:
                logger.error(f"Error fetching grade: {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Error processing grade information"
                )

        if "planned_competitive_exams" in query_params:
            query_params["planned_competitive_exams"] = process_exams(
                query_params["planned_competitive_exams"]
            )

        if "physically_handicapped" in query_params:
            query_params["physically_handicapped"] = (
                "true" if query_params["physically_handicapped"] == "Yes" else "false"
            )

        new_student_data = create_new_student_record(query_params)
        if not new_student_data:
            raise HTTPException(
                status_code=500, detail="Failed to create student record"
            )

        await create_auth_group_user_record(new_student_data, data["auth_group"])

        if data["auth_group"] == "AllIndiaStudents":
            grade_value = query_params.get("grade", "unknown")
            batch_id = f"AllIndiaStudents_{grade_value}_24_A001"  # update to 26 later str(datetime.now().year)[-2:]
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
            and (
                "batch_registration" in query_params
                and query_params["batch_registration"] is True
            )
        ):
            grade_value = query_params["grade"]
            if data["auth_group"] == "HimachalStudents":
                batch_id = f"HP-{grade_value}-Selection-25"  # update 26 later
            elif data["auth_group"] == "UttarakhandStudents":
                batch_id = f"UK-{grade_value}-Selection-25"  # update 26 later
            elif data["auth_group"] == "DelhiStudents":
                batch_id = f"DL-{grade_value}-Selection-25"  # update 26 later
            elif data["auth_group"] == "PunjabStudents":
                batch_id = f"PB-{grade_value}-Selection-25"  # update 26 later

            await create_batch_user_record(new_student_data, batch_id)

        if "grade_id" in new_student_data:
            await create_grade_user_record(new_student_data)

        if "school_name" in query_params:
            school_name = query_params["school_name"]
            district = query_params.get("district")
            # School already validated above, so this should succeed
            await create_school_user_record(
                new_student_data,
                school_name,
                district,
                data["auth_group"],
            )

        final_student_id = query_params.get("student_id", "unknown")
        logger.info(f"Successfully created student: {final_student_id}")
        return {"student_id": final_student_id, "already_exists": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_student: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating student")


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

        student_response = get_students(
            build_request(query_params={"student_id": data["student_id"]})
        )

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
        result = await update_student(build_request(body=student_data))

        logger.info("Successfully completed profile details")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing profile details: {str(e)}")
        raise HTTPException(status_code=500, detail="Error completing profile details")
