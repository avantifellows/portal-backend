from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
import helpers
import mapping
from router import (
    routes,
    school,
    enrollment_record,
    user,
    exam as exam_router,
    student_exam_record,
)
from id_generation import JNVIDGeneration
from request import build_request
from helpers import db_request_token

router = APIRouter(prefix="/student", tags=["Student"])


def build_student_exam_data(data):
    # this function builds the student-exam record object
    student_exam_data = {}
    for key in data.keys():
        if key in mapping.STUDENT_EXAM_RECORD_QUERY_PARAMS:

            # the key 'student_id' is the ID entered by the user but the 'student_id' being stored in the student-exam table is the PK of a row in the student table.
            # Hence, we retreive the PK of a student based on their 'student_id' and that is stored in the student-exam record table.
            if key == "student_id":
                student_response = get_students(
                    build_request(query_params={"student_id": data["student_id"]})
                )
                student_exam_data["student_id"] = int(student_response[0]["id"])

            # for the key 'exam_name', we have to retrieve the respective exam PK to store in the student-exam record table
            elif key == "exam_name":
                exam_response = exam_router.get_exam(
                    build_request(query_params={"name": data[key]})
                )
                if len(exam_response) != 0:
                    student_exam_data["exam_id"] = int(exam_response[0]["id"])

            # for any other key, we store the value as the user entered
            else:
                student_exam_data[key] = data[key]
    return student_exam_data


def build_enrollment_data(data):
    # this function builds the enrollment data object of a student
    enrollment_data = {}
    for key in data.keys():
        if key in mapping.ENROLLMENT_RECORD_PARAMS and key != "student_id":
            enrollment_data[key] = data[key]
    return enrollment_data


async def build_student_data(data):
    # this function builds the student data object
    student_data = {}
    for key in data.keys():
        if key in mapping.STUDENT_QUERY_PARAMS:

            # the key 'planned_competitive_exams' contains an array of exam names. Each exam PK is retrieved and stored in the student table.
            if key == "planned_competitive_exams":
                exam_ids = []
                for exam in data[key]:
                    exam_response = exam_router.get_exam(
                        build_request(query_params={"name": exam})
                    )
                    if exam_response != []:
                        exam_ids.append(exam_response[0]["id"])

                student_data[key] = exam_ids

            # for any other key, we store the value as the user entered
            else:
                student_data[key] = data[key]
    return student_data


def build_user_data(data):
    # this function builds the user data object
    user_data = {}
    for key in data.keys():
        if key in mapping.USER_QUERY_PARAMS:
            user_data[key] = data[key]
    return user_data


@router.get("/")
def get_students(request: Request):
    """
    This API returns a student or a list of students who match the criteria(s) given in the request.

    Optional Parameters:
    student_id (str), birth_date (str), category (str), stream (str).
    For extensive list of optional parameters, refer to the DB schema note on Notion.

    Returns:
    list: student data if student(s) whose details match, otherwise 404

    Example:
    > $BASE_URL/student/
    returns [data_of_all_students]

    > $BASE_URL/student/?student_id=1234
    returns [{student_data}]

    > $BASE_URL/student/?stream=PCB
    returns [data_of_all_students_with_stream_PCB]

    > $BASE_URL/student/?student_id=student_id_with_stream_PCM&stream=PCB

    returns {
        "status_code": 404,
        "detail": "No student found!",
        "headers": null
    }

    """
    query_params = helpers.validate_and_build_query_params(
        request.query_params, mapping.STUDENT_QUERY_PARAMS + mapping.USER_QUERY_PARAMS
    )

    response = requests.get(
        routes.student_db_url, params=query_params, headers=db_request_token()
    )

    if helpers.is_response_valid(response, "Student API could not fetch the student!"):
        return helpers.is_response_empty(
            response.json(), True, "Student does not exist"
        )


@router.get("/verify")
async def verify_student(request: Request, student_id: str):
    """
    This API checks if the provided student ID and the additional details match in the database.

    Parameters:
    student_id (str): The student ID to be checked.

    Other parameters:
    Example: birth_date (str), category (str), stream (str).
    For extensive list of optional parameters, refer to the DB schema note on Notion.

    Returns:
    bool: True if the details match against the student ID, otherwise False

    Example:
    > $BASE_URL/student/verify/?student_id=1234
    returns True

    > $BASE_URL/student/verify/?student_id=1234&stream=PCB
    returns True

    > $BASE_URL/student/verify/?student_id={invalid_id}
    returns {
        "status_code": 404,
        "detail": "Student ID does not exist!",
        "headers": null
    }

    > $BASE_URL/student/1234/?student_id=1234&stream=PCM
    returns {
        "status_code": 404,
        "detail": "Student ID does not exist!",
        "headers": null
    }

    """

    query_params = helpers.validate_and_build_query_params(
        request.query_params,
        mapping.STUDENT_QUERY_PARAMS + mapping.USER_QUERY_PARAMS + ["group_id"],
    )

    response = requests.get(
        routes.student_db_url,
        params={"student_id": student_id},
        headers=db_request_token(),
    )
    if helpers.is_response_valid(response):
        student_data = helpers.is_response_empty(response.json(), False)

        if student_data:
            student_data = student_data[0]
            if len(query_params) != 0:

                for key in query_params.keys():

                    if key in mapping.USER_QUERY_PARAMS:

                        if student_data["user"][key] != "":
                            if student_data["user"][key] != query_params[key]:
                                return False

                    if key in mapping.STUDENT_QUERY_PARAMS:
                        if student_data[key] != "":
                            if student_data[key] != query_params[key]:
                                return False

                    if key == "group_id":
                        response = requests.get(
                            routes.group_type_db_url,
                            params={
                                "child_id": query_params["group_id"],
                                "type": "group",
                            },
                            headers=db_request_token(),
                        )

                        if helpers.is_response_valid(response):
                            data = helpers.is_response_empty(response.json()[0], False)

                            response = requests.get(
                                routes.group_user_db_url,
                                params={
                                    "group_type_id": data["id"],
                                    "user_id": student_data["user"]["id"],
                                },
                                headers=db_request_token(),
                            )
                            if helpers.is_response_valid(response):
                                return len(response.json()) != 0
                            return False

                        raise HTTPException(
                            status_code=400,
                            detail="Group Type ID could not be retrieved",
                        )
                        # compare it with the user
            return True
        return False
    return False


@router.post("/")
async def create_student(request: Request):
    """
    This API adds a student to the database based on the values given in the request.

    Returns:
    list: student data if student(s) whose details match, otherwise 404
    """
    data = await request.body()

    # check if the query parameters sent are valid
    query_params = helpers.validate_and_build_query_params(
        data["form_data"],
        mapping.STUDENT_QUERY_PARAMS
        + mapping.USER_QUERY_PARAMS
        + mapping.ENROLLMENT_RECORD_PARAMS
        + ["id_generation"],
    )

    # if ID generation is false, the user has provided with the ID
    if data["id_generation"] == "False":

        # check if ID is part of the request
        if (
            "student_id" not in query_params
            or query_params["student_id"] == ""
            or query_params["student_id"] is None
        ):
            raise HTTPException(
                status_code=400, detail="Student ID is not part of the request data"
            )

        # check if student is already part of the database. If yes, just return the student ID
        does_student_already_exist = await verify_student(
            build_request(), query_params["student_id"]
        )
        if does_student_already_exist:
            return query_params["student_id"]

        else:
            # if student ID is not part of the database, create a new student record
            response = requests.post(
                routes.student_db_url + "/register",
                data=data["form_data"],
                headers=db_request_token(),
            )

            if helpers.is_response_valid(
                response, "Student API could not post the data!"
            ):
                created_student_data = helpers.is_response_empty(
                    response.json(), "Student API could fetch the created student"
                )

            # based on the school name, retrieve the school ID
            school_id_response = school.get_school(
                build_request(query_params={"name": data["form_data"]["school_name"]})
            )
            data["form_data"]["school_id"] = school_id_response[0]["id"]

            # create a new enrollment record for the student, based on the student ID and school ID
            enrollment_data = build_enrollment_data(data["form_data"])
            enrollment_data["student_id"] = created_student_data["id"]
            await enrollment_record.create_enrollment_record(
                build_request(body=enrollment_data)
            )

            return query_params["student_id"]

    else:
        # if ID generation is true, each group has their respective logic of generating IDs
        if data["group"] == "EnableStudents":

            id = JNVIDGeneration(query_params).get_id()

        # create a student with the generated ID
        query_params["student_id"] = id

        response = requests.post(
            routes.student_db_url, params=query_params, headers=db_request_token()
        )
        if response.status_code == 201:

            # based on the school name, retrieve the school ID
            school_id_response = school.get_school(
                build_request(query_params={"name": data["school_name"]})
            )

            data["form_data"]["school_id"] = school_id_response[0]["id"]

            # create a new enrollment record for the student, based on the student ID and school ID
            enrollment_data = build_enrollment_data(data["form_data"])
            enrollment_data["student_id"] = created_student_data["id"]

            await enrollment_record.create_enrollment_record(
                build_request(body=enrollment_data)
            )
            return id

        raise HTTPException(status_code=500, detail="Student not created!")


@router.patch("/")
async def update_student(request: Request):
    data = await request.body()
    response = requests.patch(
        routes.student_db_url + "/" + str(data["id"]),
        data=data,
        headers=db_request_token(),
    )
    if helpers.is_response_valid(response, "Student API could not post the data!"):
        return helpers.is_response_empty(
            response.json(), "Student API could fetch the created student"
        )


@router.post("/complete-profile-details")
async def complete_profile_details(request: Request):
    data = await request.json()

    helpers.validate_and_build_query_params(
        data,
        mapping.STUDENT_QUERY_PARAMS
        + mapping.USER_QUERY_PARAMS
        + mapping.ENROLLMENT_RECORD_PARAMS
        + mapping.STUDENT_EXAM_RECORD_QUERY_PARAMS,
    )

    user_data, student_data, enrollment_data, student_exam_data = (
        build_user_data(data),
        await build_student_data(data),
        build_enrollment_data(data),
        build_student_exam_data(data),
    )

    # get the PK of the student whose profile is being completed
    student_response = get_students(
        build_request(query_params={"student_id": data["student_id"]})
    )

    student_data["id"] = student_response[0]["id"]

    # update the student with the entered details
    await update_student(build_request(body=student_data))

    user_data["id"] = student_response[0]["user"]["id"]

    if len(student_exam_data) > 0:
        does_student_exam_record_exist = student_exam_record.get_student_exam_record(
            build_request(query_params={"student_id": student_response[0]["id"]})
        )
        print(does_student_exam_record_exist)
        if len(does_student_exam_record_exist) == 0:
            await student_exam_record.create_student_exam_record(
                build_request(body=student_exam_data)
            )
        else:
            await student_exam_record.update_student_exam_record(
                build_request(body=student_exam_data)
            )

    if len(user_data) > 0:
        # update the student with the entered user details
        await user.update_user(build_request(body=user_data))

    # get the enrollment record of the student
    enrollment_record_response = enrollment_record.get_enrollment_record(
        build_request(query_params={"student_id": student_response[0]["id"]})
    )

    # if school name was entered by the student, get the school ID from the school table
    if "school_name" in data:
        school_response = school.get_school(
            build_request(query_params={"name": data["school_name"]})
        )
        enrollment_data["school_id"] = school_response[0]["id"]

    # if enrollment record already exists, update with new details
    if enrollment_record_response != []:
        enrollment_data["id"] = enrollment_record_response[0]["id"]

        enrollment_record_response = await enrollment_record.update_enrollment_record(
            build_request(body=enrollment_data)
        )

    # else, create a new enrollment record for the student
    else:
        enrollment_data["student_id"] = student_response[0]["id"]

        enrollment_record_response = await enrollment_record.create_enrollment_record(
            build_request(body=enrollment_data)
        )
