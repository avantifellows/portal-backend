from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from models import Student

router = APIRouter(prefix="/student", tags=["Student"])
student_db_url = settings.db_url + "/student/"


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
