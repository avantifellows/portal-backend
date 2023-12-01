from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
import helpers
import mapping
from router import routes
from helpers import db_request_token

router = APIRouter(prefix="/teacher", tags=["Teacher"])


@router.get("/")
def get_teachers(request: Request):
    """
    This API returns a teacher or a list of teachers who match the criteria(s) given in the request.

    Optional Parameters:
    uuid (str), birth_date (str)
    For extensive list of optional parameters, refer to the DB schema note on Notion.

    Returns:
    list: teacher data if teacher(s) whose details match, otherwise 404

    Example:
    > $BASE_URL/teacher/
    returns [data_of_all_teachers]

    > $BASE_URL/teacher/?uuid=1234
    returns [{teacher_data}]

    """
    query_params = helpers.validate_and_build_query_params(
        request.query_params, mapping.TEACHER_QUERY_PARAMS + mapping.USER_QUERY_PARAMS
    )

    response = requests.get(
        routes.teacher_db_url, params=query_params, headers=db_request_token()
    )

    if helpers.is_response_valid(response, "Teacher API could not fetch the teacher!"):
        return helpers.is_response_empty(
            response.json(), True, "Teacher does not exist"
        )


@router.get("/verify")
async def verify_teacher(request: Request, teacher_id: str):
    """
    This API checks if the provided teacher ID and the additional details match in the database.

    Parameters:
    uuid (str): The teacher ID to be checked.

    Other parameters:
    Example: birth_date (str)
    For extensive list of optional parameters, refer to the DB schema note on Notion.

    Returns:
    bool: True if the details match against the teacher ID, otherwise False

    """

    query_params = helpers.validate_and_build_query_params(
        request.query_params, mapping.TEACHER_QUERY_PARAMS + mapping.USER_QUERY_PARAMS
    )

    response = requests.get(
        routes.teacher_db_url,
        params={"uuid": teacher_id},
        headers=db_request_token(),
    )
    print(response.json())
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

                    if key in mapping.TEACHER_QUERY_PARAMS:
                        if data[key] != "":
                            if data[key] != query_params[key]:
                                return False
            return True
        return False
    return False
