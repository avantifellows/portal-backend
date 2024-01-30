from fastapi import APIRouter, Request
import requests
from router import student, routes
from request import build_request
import mapping
import helpers
from helpers import db_request_token

router = APIRouter(prefix="/user", tags=["User"])


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
    > GET $BASE_URL/user/
    returns [data_of_all_users]

    > GET $BASE_URL/user/?user_id=1234
    returns [{user_data}]

    > GET $BASE_URL/user/?region=Hyderabad
    returns [data_of_all_users_with_region_hyderabad]

    > GET $BASE_URL/user/?user_id=user_id_with_stream_PCM&stream=PCB
    returns {
        "status_code": 404,
        "detail": "No student found!",
        "headers": null
    }

    """
    query_params = helpers.validate_and_build_query_params(
        request.query_params, mapping.USER_QUERY_PARAMS
    )

    response = requests.get(
        routes.user_db_url, params=query_params, headers=db_request_token()
    )

    if helpers.is_response_valid(response, "User API could not fetch the data!"):
        return helpers.is_response_empty(response.json(), False, "User does not exist!")


@router.post("/")
async def create_user(request: Request):
    """
    This API creates a new user based on the provided data.

    Parameters:
    request (Request): The request object containing the data for creating the user.

    Returns:
    dict: Returns the created user record if the creation is successful. If the creation fails, an error message is returned.

    Example:

    POST $BASE_URL/user/1234
    Request Body:
    {
        "id": 1234,
        "name": "Updated User A",
        "email": "updated_user_a@example.com"
    }
    Response:
    {
        "id": 1234,
        "name": "Updated User A",
        "email": "updated_user_a@example.com"
    }
    """
    data = await request.json()
    helpers.validate_and_build_query_params(
        data["form_data"],
        mapping.STUDENT_QUERY_PARAMS
        + mapping.USER_QUERY_PARAMS
        + mapping.ENROLLMENT_RECORD_PARAMS
        + ["id_generation"]
        + ["user_type"]  + ["region"],
    )

    if data["user_type"] == "student":
        create_student_response = await student.create_student(
            build_request(
                body={
                    "form_data": data["form_data"],
                    "id_generation": data["id_generation"],
                    "group": data["group"],
                }
            )
        )
        return create_student_response


@router.patch("/")
async def update_user(request: Request):
    """
    This API updates an existing user record based on the provided data.

    Parameters:
    request (Request): The request object containing the data for updating the user.

    Returns:
    dict: Returns the updated user record if the update is successful. If the update fails, an error message is returned.

    Example:

    PATCH $BASE_URL/user/1234
    Request Body:
    {
        "id": 1234,
        "name": "Updated User A",
        "email": "updated_user_a@example.com"
    }
    Response:
    {
        "id": 1234,
        "name": "Updated User A",
        "email": "updated_user_a@example.com"
    }
    """
    data = await request.body()
    query_params = helpers.validate_and_build_query_params(
        data, mapping.USER_QUERY_PARAMS
    )

    response = requests.patch(
        routes.user_db_url + "/" + str(query_params["id"]),
        data=query_params,
        headers=db_request_token(),
    )
    if helpers.is_response_valid(response, "User API could not patch the data!"):
        return helpers.is_response_empty(
            response.json(), False, "User API could fetch the patched user!"
        )
