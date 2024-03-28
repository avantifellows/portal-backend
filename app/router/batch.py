from fastapi import APIRouter, Request
import requests
from routes import batch_db_url
from models import BatchResponse
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
from mapping import BATCH_QUERY_PARAMS

router = APIRouter(prefix="/batch", tags=["Batch"])


@router.get("/", response_model=BatchResponse)
def get_batch(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, BATCH_QUERY_PARAMS
    )
    response = requests.get(
        batch_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "Batch API could not fetch the data!"):
        return is_response_empty(response.json()[0], True, "Batch does not exist!")
