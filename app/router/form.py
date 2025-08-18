from fastapi import APIRouter, Request
from services.form_service import (
    get_form_schema_with_enhancement,
    get_student_fields_for_form,
)
from mapping import FORM_SCHEMA_QUERY_PARAMS
from helpers import validate_and_build_query_params
from logger_config import get_logger

router = APIRouter(prefix="/form-schema", tags=["Form"])

logger = get_logger()


@router.get("/")
def get_form_schema(request: Request):
    """
    Get form schema, enhanced with dynamic data by default.
    auth_group parameter enables district/school mapping enhancement.
    """
    auth_group = request.query_params.get("auth_group")
    filtered_params = dict(request.query_params)
    if "auth_group" in filtered_params:
        del filtered_params["auth_group"]

    query_params = validate_and_build_query_params(
        filtered_params, FORM_SCHEMA_QUERY_PARAMS
    )

    logger.info(
        f"Fetching form schema with params: {query_params}, auth_group: {auth_group}"
    )

    return get_form_schema_with_enhancement(auth_group=auth_group, **query_params)


@router.get("/student")
async def get_student_fields(request: Request):
    """Get student form fields"""
    query_params = validate_and_build_query_params(
        request.query_params,
        ["number_of_fields_in_popup_form", "form_id", "student_id"],
    )

    logger.info(
        f"Getting student fields for form: {query_params['form_id']}, student: {query_params['student_id']}"
    )

    return get_student_fields_for_form(
        query_params["form_id"],
        query_params["student_id"],
        int(query_params["number_of_fields_in_popup_form"]),
    )
