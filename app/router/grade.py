from fastapi import APIRouter, Request
import requests
from app.routes import grade_db_url
from app.helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    safe_get_first_item,
)
from app.logger_config import get_logger

router = APIRouter(prefix="/grade", tags=["Grade"])
logger = get_logger()


@router.get("/")
def get_grade(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, ["id", "number"]
    )

    logger.info(f"Fetching grade with params: {query_params}")

    response = requests.get(
        grade_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Grade API could not fetch the data!"):
        grade_data = safe_get_first_item(
            response.json(), "Grade record does not exist!"
        )
        logger.info("Successfully retrieved grade data")
        return grade_data
