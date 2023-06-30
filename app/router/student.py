from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
import helpers
import mapping
from router import routes

router = APIRouter(prefix="/student", tags=["Student"])


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
        request, mapping.STUDENT_QUERY_PARAMS + mapping.USER_QUERY_PARAMS
    )
    print(query_params)
    response = requests.get(routes.student_db_url, params=query_params)
    print(response)
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
        request, mapping.STUDENT_QUERY_PARAMS + mapping.USER_QUERY_PARAMS
    )

    response = requests.get(routes.student_db_url, params={"student_id": student_id})

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


@router.post("/")
async def create_student(request: Request):
    data = await request.body()
    response = requests.post(
                    routes.student_db_url + "/register", data=data
                )
    if helpers.is_response_valid(response, "Student API could not post the data!"):
        return helpers.is_response_empty(response.json(), "Student API could fetch the created student")
