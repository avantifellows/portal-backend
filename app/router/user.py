from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from router import student
from id_generation import JNVIDGeneration

router = APIRouter(prefix="/user", tags=["User"])
user_db_url = settings.db_url + "/user"
student_db_url = settings.db_url + "/student"

STUDENT_QUERY_PARAMS = [
    "student_id",
    "father_name",
    "father_phone_number",
    "mother_name",
    "mother_phone_number",
    "category",
    "stream",
    "physically_handicapped",
    "family_income",
    "father_profession",
    "father_educational_level",
    "mother_profession",
    "mother_educational_level",
    "time_of_device_availability",
    "has_internet_access",
    "contact_hours_per_week",
    "is_dropper",
]

USER_QUERY_PARAMS = [
    "first_name",
    "last_name",
    "date_of_birth",
    "phone",
    "email",
    "region",
    "state",
]


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
        if key not in STUDENT_QUERY_PARAMS and key not in USER_QUERY_PARAMS:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = data["form_data"][key]
    print(data)
    if not data["id_generation"]:
        if data["user_type"] == "student":
            if (
                "student_id" not in query_params
                or query_params["student_id"] == ""
                or query_params["student_id"] is None
            ):
                raise HTTPException(
                    status_code=400, detail="Student ID is not part of the request data"
                )
            does_student_already_exist = student.verify_student(
                student_id=query_params["student_id"]
            )
            if does_student_already_exist:
                return query_params["student_id"]
            else:
                response = requests.post(user_db_url, params=query_params)
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
