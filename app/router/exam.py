from fastapi import APIRouter, Request
import requests
from app.routes import exam_db_url
from app.helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    safe_get_first_item,
)
from app.logger_config import get_logger

router = APIRouter(prefix="/exam", tags=["Exam"])
logger = get_logger()


@router.get("/")
def get_exam(request: Request):
    query_params = validate_and_build_query_params(request.query_params, ["id", "name"])

    logger.info(f"Fetching exam with params: {query_params}")

    response = requests.get(
        exam_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Exam API could not fetch the data!"):
        # Use safe_get_first_item instead of direct array access
        exam_data = safe_get_first_item(response.json(), "Exam record does not exist!")
        logger.info("Successfully retrieved exam data")
        return exam_data
