from fastapi import APIRouter, Request
from helpers import validate_and_build_query_params
from mapping import SCHOOL_QUERY_PARAMS, USER_QUERY_PARAMS
from services.school_service import (
    get_school,
    verify_school_comprehensive,
    get_districts_by_filters,
    get_blocks_by_filters,
    get_schools_for_dropdown_by_filters,
    get_dependant_field_mapping_for_auth_group,
)
from logger_config import get_logger

router = APIRouter(prefix="/school", tags=["School"])
logger = get_logger()


@router.get("/")
def get_school_endpoint(request: Request):
    """Get school"""
    query_params = validate_and_build_query_params(
        request.query_params, SCHOOL_QUERY_PARAMS
    )

    logger.info(f"Fetching school with params: {query_params}")
    return get_school(**query_params)


@router.get("/verify")
async def verify_school(request: Request, code: str):
    """Verify school"""
    query_params = validate_and_build_query_params(
        request.query_params, SCHOOL_QUERY_PARAMS + USER_QUERY_PARAMS
    )
    return await verify_school_comprehensive(code, query_params)


@router.get("/districts")
def get_districts(auth_group: str = None, state: str = None):
    """Get list of unique districts"""
    return get_districts_by_filters(auth_group=auth_group, state=state)


@router.get("/blocks")
def get_blocks(auth_group: str = None, state: str = None, district: str = None):
    """Get list of unique blocks"""
    return get_blocks_by_filters(auth_group=auth_group, state=state, district=district)


@router.get("/schools")
def get_schools_for_dropdown(
    auth_group: str = None, state: str = None, district: str = None, block: str = None
):
    """Get list of schools for dropdown"""
    return get_schools_for_dropdown_by_filters(
        auth_group=auth_group, state=state, district=district, block=block
    )


@router.get("/dependant-mapping/{auth_group}")
def get_dependant_field_mapping(auth_group: str, include_blocks: bool = False):
    """Generate dependantFieldMapping - thin router layer."""
    return get_dependant_field_mapping_for_auth_group(auth_group, include_blocks)
