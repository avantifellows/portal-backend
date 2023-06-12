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


def id_generation(data):
    if data["group"] == "JNVStudents":
        return JNVIDGeneration(
            data["region"], data["school_name"], data["grade"]
        ).get_id


@router.post("/")
async def create_user(request: Request):
    """
    This API writes user interaction details corresponding to a session ID.
    """
    data = await request.json()
    query_params = {}
    for key in data["form_data"].keys():
        print(key, query_params)
        if key not in STUDENT_QUERY_PARAMS and key not in USER_QUERY_PARAMS:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = data["form_data"][key]

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
            if not does_student_already_exist:
                return query_params["student_id"]
            else:
                response = requests.post(user_db_url, params=query_params)
                if response.status_code == 201:
                    return query_params["student_id"]
                raise HTTPException(status_code=500, detail="User not created!")
    else:
        if data["user_type"] == "student":
            does_student_already_exist = student.verify_student(
                email=query_params["email"], phone=query_params["phone"]
            )
            if not does_student_already_exist:
                id = id_generation(data)
                does_student_already_exist = student.verify_student(student_id=id)
                if not does_student_already_exist:
                    response = requests.post(user_db_url, params=query_params)
                    if response.status_code == 201:
                        return query_params["student_id"]
                    raise HTTPException(status_code=500, detail="User not created!")
                else:
                    id_generation(data)
            return query_params["student_id"]
