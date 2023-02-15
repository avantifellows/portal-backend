from fastapi import APIRouter, HTTPException, Request, Query
import requests
from settings import settings
from utils import form_details
from datetime import datetime
import pytz
import random

router = APIRouter(prefix="/student", tags=["Student"])
student_db_url = settings.db_url + "/student"
school_db_url = settings.db_url + "/school"

QUERY_PARAMS = [
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
    query_params = {}
    for key in request.query_params.keys():
        if key not in QUERY_PARAMS:
            return HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(student_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) == 0:
            return HTTPException(status_code=404, detail="No student found!")
        return response.json()
    return HTTPException(status_code=response.status_code, detail=response.errors)


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
    query_params = {}
    for key in request.query_params.keys():
        if key not in QUERY_PARAMS:
            return HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]
    query_params["student_id"] = student_id

    response = requests.get(student_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) == 0:
            return HTTPException(status_code=404, detail="Student ID does not exist!")
        return True
    return HTTPException(status_code=response.status_code, detail=response.errors)


def get_jnv_code(data):
    response = requests.get(
        school_db_url, params={"region": data.region, "name": data.school_name}
    )
    if response.status_code == 200:
        if len(response.json()) == 0:
            return HTTPException(
                status_code=404, detail="JNV or region does not exist!"
            )
        return response.json()
    return HTTPException(status_code=response.status_code, detail=response.errors)


def generate_three_digit_code(code):
    for _ in range(3):
        code += random.randint(0, 9)
    return code


def build_data_object(params):
    data = {}
    for field in params.keys():
        if (
            field in form_details.fields
            and params[field]
            and (params[field] != "" or params[field] is not None)
        ):
            data[field] = str(params[field])
        else:
            return HTTPException(
                status_code=400, detail="Parameter {} is invalid!".format(field)
            )
    data["created_at"] = datetime.now(pytz.timezone("Asia/Kolkata"))
    return data


@router.post("/")
async def create_student(request: Request):
    """ """
    params = await request.json()
    data = build_data_object(params)
    print(data)

    # TODO: Think about this logic. How many/what parameters are required to check if student already exists?
    does_student_already_exist = requests.get(student_db_url, params=params)
    if does_student_already_exist.status_code == 200:
        student_data = does_student_already_exist.json()
        if len(student_data) == 0:
            student_id = ""

            if data.group == "EnableStudents":
                student_id += form_details.grade_code[data.grade]
                student_id += get_jnv_code(data)  # test
                student_id += generate_three_digit_code("")
                does_generated_id_exist = verify_student(student_id=student_id)
                if does_generated_id_exist:
                    return student_id

                is_student_added, number_of_loops = False, 0
                if not is_student_added or number_of_loops < 1000:
                    if not does_generated_id_exist:
                        is_student_added = True
                        # add ID to db
                        return student_id
                    else:
                        student_id[:-3] += generate_three_digit_code("")
                        does_generated_id_exist = verify_student(student_id=student_id)

        return student_data["student_id"]

    return HTTPException(
        status_code=does_student_already_exist.status_code,
        detail=does_student_already_exist.errors,
    )
