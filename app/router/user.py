from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from router import student
from id_generation import JNVIDGeneration
from request import build_request

router = APIRouter(prefix="/user", tags=["User"])
user_db_url = settings.db_url + "/user"
student_db_url = settings.db_url + "/student"
enrollment_record_db_url = settings.db_url + "/enrollment-record"

STUDENT_QUERY_PARAMS = [
    "student_id",
    "father_name",
    "father_phone",
    "mother_name",
    "mother_phone",
    "category",
    "stream",
    "physically_handicapped",
    "family_income",
    "father_profession",
    "father_education_level",
    "mother_profession",
    "mother_education_level",
    "time_of_device_availability",
    "has_internet_access",
    "contact_hours_per_week",
    "is_dropper",
    "primary_smartphone_owner_profession",
    "primary_smartphone_owner",
]

USER_QUERY_PARAMS = [
    "first_name",
    "last_name",
    "date_of_birth",
    "phone",
    "whatsapp_phone",
    "email",
    "region",
    "state",
    "district",
    "gender",
    "consent_check",
]

ENROLLMENT_RECORD_PARAMS = ["grade", "board_medium", "school_code", "school_name"]


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
    query_params = {}
    for key in request.query_params.keys():
        if key not in USER_QUERY_PARAMS:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(user_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) == 0:
            return HTTPException(status_code=404, detail="No user found!")
        return response.json()
    raise HTTPException(status_code=404, detail="No user found!")


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
            key not in STUDENT_QUERY_PARAMS
            and key not in USER_QUERY_PARAMS
            and key not in ENROLLMENT_RECORD_PARAMS
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
                build_request(query_params={"student_id": query_params["student_id"]}),
                student_id=query_params["student_id"],
            )
            if does_student_already_exist:
                return query_params["student_id"]
            else:
                if (
                    "first_name" in data["form_data"]
                    or "last_name" in data["form_data"]
                ):
                    data["form_data"]["full_name"] = (
                        data["form_data"]["first_name"]
                        + " "
                        + data["form_data"]["last_name"]
                    )
                response = requests.post(
                    student_db_url + "/register", data=data["form_data"]
                )
                if response.status_code == 201:
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
    student_data, user_data, enrollment_data = {}, {}, {}
    for key in data.keys():
        if key in STUDENT_QUERY_PARAMS:
            if key in ["has_internet_access"]:
                student_data[key] = str(data[key] == "Yes").lower()
            else:
                student_data[key] = data[key]
        elif key in USER_QUERY_PARAMS:
            user_data[key] = data[key]
        elif key in ENROLLMENT_RECORD_PARAMS:
            enrollment_data[key] = data[key]
        else:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )

    if "first_name" in user_data:
        user_data["full_name"] = user_data["first_name"] + " "
    if "last_name" in user_data:
        user_data["full_name"] = user_data["last_name"]

    response = requests.get(student_db_url, params={"student_id": data["student_id"]})
    data = response.json()[0]
    if response.status_code == 200:
        patched_data = requests.patch(
            student_db_url + "/" + str(data["id"]), data=student_data
        )

        if patched_data.status_code != 200:
            raise HTTPException(status_code=500, detail="Student data not patched!")
    else:
        raise HTTPException(status_code=404, detail="Student not found!")

    if len(user_data) > 0:
        print(user_data, data)
        patched_data = requests.patch(
            user_db_url + "/" + str(data["user"]["id"]), data=user_data
        )
        if patched_data.status_code != 200:
            raise HTTPException(status_code=500, detail="User data not patched!")

    if len(enrollment_data) > 0:
        enrollment_response = requests.get(
            enrollment_record_db_url, params={"student_id": data["student_id"]}
        )
        if enrollment_response.status_code == 200:
            data = enrollment_response.json()[0]
            patched_data = requests.patch(
                enrollment_record_db_url + "/" + str(data["id"]), data=enrollment_data
            )

            if patched_data.status_code != 200:
                raise HTTPException(
                    status_code=500, detail="Enrollment data not patched!"
                )
        else:
            raise HTTPException(status_code=404, detail="Enrollment not found!")
