from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings

router = APIRouter(prefix="/student", tags=["Student"])
student_db_url = settings.db_url + "/student"

QUERY_PARAMS = [
    "student_id",
    "birth_date",
    "phone_number",
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
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(student_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) == 0:
            return HTTPException(status_code=404, detail="No student found!")
        return response.json()
    raise HTTPException(status_code=404, detail="No student found!")


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
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]
    query_params["student_id"] = student_id

    response = requests.get(student_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) == 0:
            return False
        return True
    raise HTTPException(status_code=404, detail="Student ID does not exist!")
