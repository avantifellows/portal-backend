from fastapi import APIRouter, Request
import requests
from routes import batch_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    safe_get_first_item,
)
from mapping import BATCH_QUERY_PARAMS
from logger_config import get_logger

router = APIRouter(prefix="/batch", tags=["Batch"])
logger = get_logger()


@router.get("/")
def get_batch(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, BATCH_QUERY_PARAMS
    )

    logger.info(f"Fetching batch with params: {query_params}")

    response = requests.get(
        batch_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Batch API could not fetch the data!"):
        # Use safe_get_first_item instead of direct array access
        batch_data = safe_get_first_item(response.json(), "Batch does not exist!")
        logger.info("Successfully retrieved batch data")
        return batch_data
