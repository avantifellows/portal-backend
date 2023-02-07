from fastapi import APIRouter, HTTPException, Request, Path
import requests
from settings import settings
from datetime import datetime
import pytz
from models import StudentRequest
from utils import form_details
from typing import Optional
import random
from models import Student

router = APIRouter(prefix="/student", tags=["Student"])
student_db_url = settings.db_url + "/student/"
school_db_url = settings.db_url + "/school"


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
    for field in form_details.fields:

        if (
            field in params.keys()
            and params[field]
            and (params[field] != "" or params[field] is not None)
        ):
            data[field] = str(params[field])
    data["created_at"] = datetime.now(pytz.timezone("Asia/Kolkata"))
    return data


@router.get("/")
def index(student: Student):
    response = requests.get(student_db_url, params=dict(student))
    if response.status_code == 200:
        if len(response.json()) == 0:
            return HTTPException(status_code=404, detail="No student found!")
        return response.json()
    return HTTPException(status_code=response.status_code, detail=response.errors)


@router.get("/{student_id}")
def get_student(student_id: str):
    """
    This API checks if the provided student ID exists in the database.
    Additionally, if any other details need to be matched in the database, these details can be sent as query parameters.

    Parameters:
    student_id (str): The student ID to be checked.

    Optional parameters:
    Example: birth_date (str), category (str), stream (str).
    For extensive list of optional parameters, refer to the DB schema note on Notion.

    Returns:
    list: Returns student details if the student ID exists in the database (and optional parameters match, if they are provided), 404 otherwise.

    Example:
    > $BASE_URL/student/1234
    returns [{student_data}]

    > $BASE_URL/student/{invalid_id}
    returns {
        "status_code": 404,
        "detail": "Student ID does not exist!",
        "headers": null
    }

    > $BASE_URL/student/1234/?stream=PCB&catgeory=Gen
    returns [{student_data}]

    """
    response = requests.get(student_db_url, params={"student_id": student_id})

    if response.status_code == 200:
        if len(response.json()) == 0:
            return HTTPException(status_code=404, detail="Student ID does not exist!")
        return response.json()
    return HTTPException(status_code=response.status_code, detail=response.errors)


@router.post("/")
async def create_student(request: Request):
    params = await request.json()
    data = build_data_object(params)

    does_student_already_exist = index(request=request)
    if does_student_already_exist.status_code == 200:
        student_id = does_student_already_exist.json()
        if len(student_id) == 0:

            student_id += form_details.grade_code[data.grade]
            student_id += get_jnv_code(data)  # test
            student_id += generate_three_digit_code("")
            does_generated_id_exist = requests.get(
                student_db_url, params={"student_id": student_id}
            )

            is_student_added, number_of_loops = False, 0
            if not is_student_added or number_of_loops < 1000:
                if len(does_generated_id_exist.json()) == 0:
                    is_student_added = True
                    # add ID to db
                    return student_id
                else:
                    student_id[:-3] += generate_three_digit_code("")
                    does_generated_id_exist = requests.get(
                        student_db_url, params={"student_id": student_id}
                    )

        return student_id

    return HTTPException(
        status_code=does_student_already_exist.status_code,
        detail=does_student_already_exist.errors,
    )
