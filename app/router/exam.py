from fastapi import APIRouter, Request
import requests
from routes import exam_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)

router = APIRouter(prefix="/exam", tags=["Exam"])


@router.get("/")
def get_exam(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, ["id", "name"]
    )
    response = requests.get(
        exam_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "Exam API could not fetch the data!"):
        return is_response_empty(
            response.json()[0], True, "Exam record does not exist!"
        )
