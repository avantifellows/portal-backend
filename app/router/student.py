from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings


router = APIRouter(prefix="/student", tags=["Student"])
student_db_url = settings.db_url + "/student/"


@router.get("/{student_id}")
def index(student_id: str, request: Request):
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
    extra_parameters = dict(request.query_params)
    query_params = {"student_id": student_id}
    response = requests.get(student_db_url, params=query_params)

    if response.status_code == 200:
        if len(response.json()) == 0:
            return HTTPException(status_code=404, detail="Student ID does not exist!")

        elif len(extra_parameters) != 0:
            query_params.update(extra_parameters)
            response = requests.get(student_db_url, params=query_params)
            if response.status_code == 200:
                if len(response.json()) == 0:
                    return HTTPException(
                        status_code=404, detail="Paramters do not match!"
                    )
                return response.json()
            return HTTPException(
                status_code=response.status_code, detail=response.errors
            )

        return response.json()
    return HTTPException(status_code=response.status_code, detail=response.errors)
