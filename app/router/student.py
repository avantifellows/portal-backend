from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
import helpers
import mapping
from router import routes, school, enrollment_record, user
from id_generation import JNVIDGeneration
from request import build_request
from logger_config import get_logger
from helpers import db_request_token

router = APIRouter(prefix="/student", tags=["Student"])
logger = get_logger()


def build_enrollment_data(data):
    enrollment_data = {}
    for key in data.keys():
        if key in mapping.ENROLLMENT_RECORD_PARAMS and key != "student_id":
            enrollment_data[key] = data[key]
    return enrollment_data


def build_student_data(data):
    student_data = {}
    for key in data.keys():
        if key in mapping.STUDENT_QUERY_PARAMS:
            student_data[key] = data[key]
    return student_data


def build_user_data(data):
    user_data = {}
    for key in data.keys():
        if key in mapping.USER_QUERY_PARAMS:
            user_data[key] = data[key]
    return user_data


def id_generation(data):
    if data["group"] == "JNVStudents":
        counter = settings.JNV_counter
        if counter > 0:
            JNV_Id = JNVIDGeneration(
                data["region"], data["school_name"], data["grade"]
            ).get_id
            counter -= 1
            return JNV_Id
        raise HTTPException(
            status_code=400, detail="Student ID could not be generated. Max loops hit!"
        )


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
        request.query_params, mapping.STUDENT_QUERY_PARAMS + mapping.USER_QUERY_PARAMS
    )

    logger.info(f"Verifying student: {student_id}")

    response = requests.get(
        routes.student_db_url,
        params={"student_id": student_id},
        headers=db_request_token(),
    )

    if helpers.is_response_valid(response):
        data = helpers.is_response_empty(response.json(), False)

        if data:
            data = data[0]
            if len(query_params) != 0:

                for key in query_params.keys():

                    if key in mapping.USER_QUERY_PARAMS:
                        if data["user"][key] != "":
                            if data["user"][key] != query_params[key]:
                                return False

                    if key in mapping.STUDENT_QUERY_PARAMS:
                        if data[key] != "":
                            if data[key] != query_params[key]:
                                return False
            return True
        return False
    return False


@router.post("/")
async def create_student(request: Request):
    data = await request.body()
    print("student:", data)
    query_params = helpers.validate_and_build_query_params(
        data["form_data"],
        mapping.STUDENT_QUERY_PARAMS
        + mapping.USER_QUERY_PARAMS
        + mapping.ENROLLMENT_RECORD_PARAMS
        + ["id_generation"],
    )

    if data["id_generation"] == "False":
        if (
            "student_id" not in query_params
            or query_params["student_id"] == ""
            or query_params["student_id"] is None
        ):
            raise HTTPException(
                status_code=400, detail="Student ID is not part of the request data"
            )

        # check if student is already part of the ID. If yes, just return the student ID
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
            print("here")
            # create a new enrollment record for the student, based on the student ID and school ID
            enrollment_data = build_enrollment_data(data["form_data"])
            enrollment_data["student_id"] = created_student_data["id"]
            print(enrollment_data)
            await enrollment_record.create_enrollment_record(
                build_request(body=enrollment_data)
            )

            return query_params["student_id"]

    else:
        if (
            "email" not in query_params
            or query_params["email"] == ""
            or query_params["email"] is None
        ) or (
            "phone" not in query_params
            or query_params["phone"] == ""
            or query_params["phone"] is None
        ):
            raise HTTPException(
                status_code=400, detail="Email/Phone is not part of the request data"
            )

        does_user_already_exist = user.get_users(
            build_request(
                query_params={
                    "email": query_params["email"],
                    "phone": query_params["phone"],
                }
            )
        )

        if not does_user_already_exist:
            while True:
                id = id_generation(data)
                does_student_already_exist = verify_student(
                    build_request(), student_id=id
                )
                if not does_student_already_exist:
                    response = requests.post(
                        routes.user_db_url,
                        params=query_params,
                        headers=db_request_token(),
                    )
                    if response.status_code == 201:
                        return query_params["student_id"]
                    raise HTTPException(status_code=500, detail="User not created!")

        else:
            response = get_students(
                build_request(
                    query_params={"user_id": does_user_already_exist["user_id"]}
                )
            )
            if response.status_code == 200:
                return response["student_id"]
            raise HTTPException(
                status_code=404, detail="User and student details do not match!"
            )


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
        + mapping.ENROLLMENT_RECORD_PARAMS,
    )

    user_data, student_data, enrollment_data = (
        build_user_data(data),
        build_student_data(data),
        build_enrollment_data(data),
    )

    # get the PK of the student whose profile is being completed
    student_response = get_students(
        build_request(query_params={"student_id": data["student_id"]})
    )

    student_data["id"] = student_response[0]["id"]

    # update the student with the entered details
    await update_student(build_request(body=student_data))

    user_data["id"] = student_response[0]["user"]["id"]

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
