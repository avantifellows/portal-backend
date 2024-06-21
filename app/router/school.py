from fastapi import APIRouter, Request
import requests
from routes import school_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from mapping import SCHOOL_QUERY_PARAMS

router = APIRouter(prefix="/school", tags=["School"])


@router.get("/")
def get_school(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, SCHOOL_QUERY_PARAMS
    )
    response = requests.get(
        school_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "School API could not fetch the data!"):
        print(request.query_params)
        return is_response_empty(response.json()[0], True, "School does not exist")
