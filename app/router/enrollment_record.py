from fastapi import APIRouter, Request
import requests
from router import routes
import helpers
import mapping

router = APIRouter(prefix="/enrollment-record", tags=["Enrollment Record"])


@router.get("/")
def get_enrollment_record(request: Request):
    """
    This API returns an enrollment record or a list of enrollment records which match the criteria(s) given in the request.

    Returns:
    list: enrollment data if enrollment record(s) details match, otherwise 404

    Example:
    > $BASE_URL/enrollment-record/
    returns [data_of_all_enrollment_records]

    > $BASE_URL/enrollment-record/?student_id=1234
    returns [{enrollment_data_of_student_1234}]

    > $BASE_URL/enrollment-record/?school_id=123
    returns [enrollment_data_of_school_123]

    """
    query_params = helpers.validate_and_build_query_params(
        request, mapping.ENROLLMENT_RECORD_PARAMS
    )
    response = requests.get(routes.enrollment_record_db_url, params=query_params)

    if helpers.is_response_valid(response, "Enrollment API could not fetch the data!"):

        return helpers.is_response_empty(
            response.json(), False, "Enrollment record does not exist"
        )


@router.post("/")
async def create_enrollment_record(request: Request):
    data = await request.body()
    response = requests.post(routes.enrollment_record_db_url, data=data)
    if helpers.is_response_valid(response, "Enrollment API could not post the data!"):
        return helpers.is_response_empty(
            response.json(), "Enrollment API could not fetch the created record!"
        )

@router.patch("/")
async def update_enrollment_record(request: Request):
    data = await request.body()
    print(data)
    response = requests.post(routes.enrollment_record_db_url, data=data)
    if helpers.is_response_valid(response, "Enrollment API could not post the data!"):
        return helpers.is_response_empty(
            response.json(), "Enrollment API could not fetch the created record!"
        )