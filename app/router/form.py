from fastapi import APIRouter, Request, HTTPException
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
        ["number_of_fields_in_popup_form", "form_id", "student_id", "user_id"],
    )

    student_identifier = query_params.get("user_id") or query_params.get("student_id")
    identifier_type = "user_id" if query_params.get("user_id") else "student_id"

    if not student_identifier:
        raise HTTPException(
            status_code=400,
            detail="user_id or student_id is required for student form fields",
        )

    logger.info(
        f"Getting student fields for form: {query_params['form_id']}, {identifier_type}: {student_identifier}"
    )

    return get_student_fields_for_form(
        query_params["form_id"],
        student_identifier,
        int(query_params["number_of_fields_in_popup_form"]),
        identifier_type,
    )
