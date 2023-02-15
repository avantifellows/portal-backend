from fastapi import APIRouter, HTTPException
import requests
from settings import settings
from models import Student

router = APIRouter(prefix="/student", tags=["Student"])
student_db_url = settings.db_url + "/student"


@router.get("/")
def get_students(student: Student, student_id: str = None):
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

    > $BASE_URL/student/
    body: {"stream":"PCB"}
    returns [data_of_all_students_with_stream_PCB]

    > $BASE_URL/student/?student_id=student_id_with_stream_PCM
    body: {"stream":"PCB"}

    returns {
        "status_code": 404,
        "detail": "No student found!",
        "headers": null
    }

    """
    query_params = {}
    student_attributes = student.dict(exclude_unset=True)
    for key in student_attributes.keys():
        query_params[key] = student_attributes[key]
    if student_id:
        query_params["student_id"] = student_id

    response = requests.get(student_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) == 0:
            return HTTPException(status_code=404, detail="No student found!")
        return response.json()
    return HTTPException(status_code=response.status_code, detail=response.errors)


@router.get("/verify")
def verify_student(student_id: str, student: Student):
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
    body: {"stream":"PCB"}
    returns True

    > $BASE_URL/student/verify/?student_id={invalid_id}
    returns {
        "status_code": 404,
        "detail": "Student ID does not exist!",
        "headers": null
    }

    > $BASE_URL/student/1234/?student_id=1234
    body: {"stream":"PCM"}
    returns {
        "status_code": 404,
        "detail": "Student ID does not exist!",
        "headers": null
    }

    """
    query_params = {}
    student_attributes = student.dict(exclude_unset=True)
    for key in student_attributes.keys():
        query_params[key] = student_attributes[key]
    if student_id:
        query_params["student_id"] = student_id

    response = requests.get(student_db_url, params=query_params)

    if response.status_code == 200:
        if len(response.json()) == 0:
            return HTTPException(status_code=404, detail="Student ID does not exist!")
        return True
    return HTTPException(status_code=response.status_code, detail=response.errors)
