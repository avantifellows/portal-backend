from fastapi import APIRouter, Request
import requests
from routes import grade_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)

router = APIRouter(prefix="/grade", tags=["Grade"])


@router.get("/")
def get_grade(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, ["id", "number"]
    )
    response = requests.get(
        grade_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "Grade API could not fetch the data!"):
        return is_response_empty(
            response.json()[0], True, "Grade record does not exist!"
        )
