from fastapi import APIRouter, Request
import requests
from router import routes
import helpers
import mapping
from helpers import db_request_token

router = APIRouter(prefix="/enrollment-record", tags=["Enrollment Record"])


@router.get("/")
def get_enrollment_record(request: Request):
    """
    This API retrieves enrollment record data based on the provided query parameters.

    Parameters:
    request (Request): The request object containing the query parameters.

    Returns:
    list: Returns the enrollment record data that matches the provided query parameters. If no enrollment record matches the parameters, an error message is returned.

    Example:

        GET $BASE_URL/get_enrollment_record?id=1234&student_id=5678
        Response:
        {
        "status_code": 200,
        "detail": "Enrollment record data retrieved successfully!",
        "enrollment_data": [{matching_enrollment_data}],
        "headers": null
        }

        GET $BASE_URL/get_enrollment_record?student_id=5678
        Response:
        {
        "status_code": 404,
        "detail": "Enrollment record does not exist",
        "headers": null
        }
    """
    query_params = helpers.validate_and_build_query_params(
        request.query_params, mapping.ENROLLMENT_RECORD_PARAMS
    )
    response = requests.get(
        routes.enrollment_record_db_url, params=query_params, headers=db_request_token()
    )

    if helpers.is_response_valid(response, "Enrollment API could not fetch the data!"):
        return helpers.is_response_empty(
            response.json(), False, "Enrollment record does not exist!"
        )


@router.post("/")
async def create_enrollment_record(request: Request):
    """
    This API creates a new enrollment record based on the provided request data.

    Parameters:
    request (Request): The request object containing the enrollment record data.

    Returns:
    dict: Returns the created enrollment record data if the creation is successful. If the creation fails, an error message is returned.

    Example:

        POST $BASE_URL/create_enrollment_record
        Request Body:
        {
        "student_id": 1234,
        "batch_id": 5678,
        "enrollment_date": "2023-06-22",
        ...
        }
        Response:
        {
        "status_code": 200,
        "detail": "Enrollment record created successfully!",
        "enrollment_record": {created_enrollment_data},
        "headers": null
        }

        POST $BASE_URL/create_enrollment_record
        Request Body:
        {
        "student_id": 1234,
        "batch_id": 5678,
        "enrollment_date": "2023-06-22",
        ...
        }
        Response:
        {
        "status_code": 500,
        "detail": "Enrollment API could not fetch the created record!",
        "headers": null
        }
    """
    data = await request.body()
    response = requests.post(
        routes.enrollment_record_db_url, data=data, headers=db_request_token()
    )
    if helpers.is_response_valid(response, "Enrollment API could not post the data!"):
        return helpers.is_response_empty(
            response.json(), "Enrollment API could not fetch the created record!"
        )


@router.patch("/")
async def update_enrollment_record(request: Request):
    """
    This API updates an existing enrollment record based on the provided request data.

    Parameters:
    request (Request): The request object containing the updated enrollment record data.

    Returns:
    dict: Returns the updated enrollment record data if the update is successful. If the update fails, an error message is returned.

    Example:

        PATCH $BASE_URL/update_enrollment_record
        Request Body:
        {
        "id": 1234,
        "enrollment_date": "2023-06-23",
        ...
        }
        Response:
        {
        "status_code": 200,
        "detail": "Enrollment record updated successfully!",
        "enrollment_record": {updated_enrollment_data},
        "headers": null
        }

        PATCH $BASE_URL/update_enrollment_record
        Request Body:
        {
        "id": 1234,
        "enrollment_date": "2023-06-23",
        ...
        }
        Response:
        {
        "status_code": 500,
        "detail": "Enrollment API could not fetch the patched record!",
        "headers": null
        }
    """
    data = await request.body()
    response = requests.patch(
        routes.enrollment_record_db_url + "/" + str(data["id"]),
        data=data,
        headers=db_request_token(),
    )
    if helpers.is_response_valid(response, "Enrollment API could not patch the data!"):
        return helpers.is_response_empty(
            response.json(), "Enrollment API could not fetch the patched record!"
        )
