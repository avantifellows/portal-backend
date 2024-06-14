from fastapi import APIRouter, Request
import requests
from routes import enrollment_record_db_url
from models import EnrollmentRecordResponse
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from mapping import ENROLLMENT_RECORD_PARAMS

router = APIRouter(prefix="/enrollment-record", tags=["Enrollment Record"])


@router.get("/", response_model=EnrollmentRecordResponse)
def get_enrollment_record(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, ENROLLMENT_RECORD_PARAMS
    )
    response = requests.get(
        enrollment_record_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Enrollment API could not fetch the data!"):
        return is_response_empty(
            response.json(), False, "Enrollment record does not exist!"
        )


@router.post("/")
async def create_enrollment_record(request: Request):
    data = await request.body()
    response = requests.post(
        enrollment_record_db_url, data=data, headers=db_request_token()
    )
    if is_response_valid(response, "Enrollment API could not post the data!"):
        return is_response_empty(
            response.json(), False, "Enrollment API could not fetch the created record!"
        )
