from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from router import student, routes
from id_generation import JNVIDGeneration
from request import build_request
import mapping
import helpers

router = APIRouter(prefix="/user", tags=["User"])

def build_enrollment_data(data):
    enrollment_data = {}
    for key in data.keys():
        if key in mapping.ENROLLMENT_RECORD_PARAMS:
            enrollment_data[key] = data[key]
    return enrollment_data


def build_student_data(data):
    student_data = {}
    for key in data.keys():
        if key in mapping.STUDENT_QUERY_PARAMS:
            if key in ["has_internet_access"]:
                student_data[key] = str(data[key] == "Yes").lower()
            else:
                student_data[key] = data[key]
    return student_data


def build_user_data(data):
    user_data = {}
    for key in data.keys():
        if key in mapping.USER_QUERY_PARAMS:
            user_data[key] = data[key]
    return user_data


@router.get("/")
def get_users(request: Request):
    """
    This API returns a user or a list of users who match the criteria(s) given in the request.

    Optional Parameters:
    phone (str), date_of_birth (str), email (str).
    For extensive list of optional parameters, refer to the DB schema note on Notion.

    Returns:
    list: user data if user(s) whose details match, otherwise 404

    Example:
    > $BASE_URL/user/
    returns [data_of_all_users]

    > $BASE_URL/user/?user_id=1234
    returns [{user_data}]

    > $BASE_URL/user/?region=Hyderabad
    returns [data_of_all_users_with_region_hyderabad]

    > $BASE_URL/user/?user_id=user_id_with_stream_PCM&stream=PCB
    returns {
        "status_code": 404,
        "detail": "No student found!",
        "headers": null
    }

    """
    query_params = helpers.validate_and_build_query_params(request, mapping.USER_QUERY_PARAMS)

    response = requests.get(routes.user_db_url, params=query_params)
    if helpers.is_response_valid(response,"User API could not fetch the data!"):
        return helpers.is_response_empty(response.json(), False, "User does not exist!")


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


@router.post("/")
async def create_user(request: Request):
    """
    This API writes user interaction details corresponding to a session ID.
    """
    data = await request.json()
    query_params = {}

    for key in data["form_data"].keys():
        if (
            key not in mapping.STUDENT_QUERY_PARAMS
            and key not in mapping.USER_QUERY_PARAMS
            and key not in mapping.ENROLLMENT_RECORD_PARAMS
        ):
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = data["form_data"][key]

    if data["id_generation"] == "false":
        if data["user_type"] == "student":
            if (
                "student_id" not in query_params
                or query_params["student_id"] == ""
                or query_params["student_id"] is None
            ):
                raise HTTPException(
                    status_code=400, detail="Student ID is not part of the request data"
                )

            does_student_already_exist = await student.verify_student(
                build_request(), query_params["student_id"]
            )
            if does_student_already_exist:
                return query_params["student_id"]
            else:
                if "first_name" in data["form_data"]:
                    data["form_data"]["full_name"] = (
                        data["form_data"]["first_name"] + " "
                    )
                if "last_name" in data["form_data"]:
                    data["form_data"]["full_name"] = data["form_data"]["last_name"]

                response = requests.post(
                    routes.student_db_url + "/register", data=data["form_data"]
                )
                if response.status_code == 201:
                    school_response = requests.get(
                        routes.school_db_url, params={"name": data["form_data"]["school_name"]}
                    )
                    data["form_data"]["school_id"] = school_response.json()[0]["id"]
                    enrollment_data = build_enrollment_data(data["form_data"])

                    if len(enrollment_data) > 0:
                        enrollment_data["student_id"] = response.json()["id"]

                        print(enrollment_data)
                        enrollment_response = requests.post(
                            routes.enrollment_record_db_url, data=enrollment_data
                        )
                        if enrollment_response.status_code == 201:
                            return query_params["student_id"]
                raise HTTPException(status_code=500, detail="User not created!")

    else:
        if data["user_type"] == "student":
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
                    status_code=400,
                    detail="Email/Phone is not part of the request data",
                )
            does_user_already_exist = get_users(
                email=query_params["email"], phone=query_params["phone"]
            )
            if not does_user_already_exist:
                while True:
                    id = id_generation(data)
                    does_student_already_exist = student.verify_student(student_id=id)
                    if not does_student_already_exist:
                        response = requests.post(user_db_url, params=query_params)
                        if response.status_code == 201:
                            return query_params["student_id"]
                        raise HTTPException(status_code=500, detail="User not created!")

            else:
                response = student.get_students(does_user_already_exist["user_id"])
                if response.status_code == 200:
                    return response["student_id"]
                raise HTTPException(status_code=500, detail="User not created!")


@router.post("/complete-profile-details")
async def complete_profile_details(request: Request):
    data = await request.json()

    for key in data.keys():
        if (
            key not in mapping.STUDENT_QUERY_PARAMS
            and key not in mapping.USER_QUERY_PARAMS
            and key not in mapping.ENROLLMENT_RECORD_PARAMS
        ):
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )

    user_data, student_data, enrollment_data = (
        build_user_data(data),
        build_student_data(data),
        build_enrollment_data(data),
    )

    if "first_name" in user_data:
        user_data["full_name"] = user_data["first_name"] + " "
    if "last_name" in user_data:
        user_data["full_name"] = user_data["last_name"]

    response = requests.get(routes.student_db_url, params={"student_id": data["student_id"]})

    if response.status_code == 200:
        data = response.json()
        patched_data = requests.patch(
            routes.student_db_url + "/" + str(data["id"]), data=student_data
        )

        if patched_data.status_code != 200:
            raise HTTPException(status_code=500, detail="Student data not patched!")
    else:
        raise HTTPException(status_code=404, detail="Student not found!")

    if len(user_data) > 0:

        data = response.json()[0]
        patched_data = requests.patch(
            routes.user_db_url + "/" + str(data["user"]["id"]), data=user_data
        )
        if patched_data.status_code != 200:
            raise HTTPException(status_code=500, detail="User data not patched!")

    if len(enrollment_data) > 0:
        print(enrollment_data)
        data = response.json()[0]
        enrollment_response = requests.get(
            routes.enrollment_record_db_url, params={"student_id": data["student_id"]}
        )
        if enrollment_response.status_code == 200:
            data = enrollment_response.json()[0]
            patched_data = requests.patch(
                routes.enrollment_record_db_url + "/" + str(data["id"]), data=enrollment_data
            )

            if patched_data.status_code != 200:
                raise HTTPException(
                    status_code=500, detail="Enrollment data not patched!"
                )
        else:
            raise HTTPException(status_code=404, detail="Enrollment not found!")
