from fastapi import APIRouter, Request
import requests
from routes import enrollment_record_db_url
from helpers import (
    db_request_token,
    is_response_valid,
    is_response_empty,
)

router = APIRouter(prefix="/enrollment-record", tags=["Enrollment Record"])


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
