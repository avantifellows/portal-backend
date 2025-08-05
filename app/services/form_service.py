"""Form service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from logger_config import get_logger
from routes import form_db_url, school_db_url
from helpers import db_request_token, is_response_valid, safe_get_first_item
from mapping import FORM_SCHEMA_QUERY_PARAMS, authgroup_state_mapping

logger = get_logger()


def get_form_schema_by_id(form_id: str) -> Optional[Dict[str, Any]]:
    """Get form schema by ID."""
    return get_form_schema(id=form_id)


def get_form_schema(**params) -> Optional[Dict[str, Any]]:
    """Get form schema with flexible parameters."""
    # Filter out None values and validate against allowed params
    query_params = {
        k: v
        for k, v in params.items()
        if v is not None and k in FORM_SCHEMA_QUERY_PARAMS
    }

    logger.info(f"Fetching form schema with params: {query_params}")

    response = requests.get(
        form_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Form API could not fetch the data!"):
        form_data = safe_get_first_item(response.json(), "Form schema does not exist!")
        logger.info("Successfully retrieved form schema")
        return form_data

    return None


def enhance_form_schema_with_dynamic_data(
    form_data: Dict[str, Any], auth_group: str
) -> Dict[str, Any]:
    """
    Enhance form schema with dynamic data from database.
    This replaces frontend form enhancement logic for better performance and reliability.
    """
    if not form_data or not form_data.get("attributes") or not auth_group:
        return form_data

    if auth_group not in authgroup_state_mapping:
        logger.warning(f"Unknown auth_group for form enhancement: {auth_group}")
        return form_data

    state = authgroup_state_mapping[auth_group]
    attributes = form_data["attributes"]

    # Check what fields need enhancement
    needs_district_school = _has_field(attributes, "district") and _has_field(
        attributes, "school_name"
    )
    needs_district_block_school = (
        _has_field(attributes, "district")
        and _has_field(attributes, "block_name")
        and _has_field(attributes, "school_name")
    )
    needs_colleges = _has_field(attributes, "college")
    needs_states = _has_field(attributes, "state")

    if needs_district_block_school:
        _enhance_with_district_block_school_mapping(attributes, auth_group, state)
    elif needs_district_school:
        _enhance_with_district_school_mapping(attributes, auth_group, state)

    if needs_colleges:
        _enhance_with_colleges(attributes)

    if needs_states:
        _enhance_with_states(attributes)

    logger.info(f"Enhanced form schema for auth_group: {auth_group}")
    return form_data


def _has_field(attributes: Dict[str, Any], field_key: str) -> bool:
    """Check if form has a specific field."""
    return any(attr.get("key") == field_key for attr in attributes.values())


def _find_field_by_key(
    attributes: Dict[str, Any], field_key: str
) -> Optional[Dict[str, Any]]:
    """Find field by key in attributes."""
    for attr in attributes.values():
        if attr.get("key") == field_key:
            return attr
    return None


def _enhance_with_district_school_mapping(
    attributes: Dict[str, Any], auth_group: str, state: str
):
    """Enhance form with district -> school mapping."""
    try:
        # Get schools data for this state
        response = requests.get(
            school_db_url, params={"state": state}, headers=db_request_token()
        )

        if not is_response_valid(response):
            logger.error(f"Failed to fetch schools data for state: {state}")
            return

        schools_data = response.json()
        if not isinstance(schools_data, list):
            schools_data = [schools_data]

        # Build district options and mapping
        districts = set()
        district_school_mapping = {}

        for school in schools_data:
            district = school.get("district")
            school_name = school.get("name")

            if not district or not school_name:
                continue

            districts.add(district)

            if district not in district_school_mapping:
                district_school_mapping[district] = {"en": [], "hi": []}

            district_school_mapping[district]["en"].append(school_name)
            district_school_mapping[district]["hi"].append(school_name)

        # Sort data
        districts = sorted(list(districts))
        for district_data in district_school_mapping.values():
            district_data["en"].sort()
            district_data["hi"].sort()

        # Update district field options
        district_field = _find_field_by_key(attributes, "district")
        if district_field:
            district_field["options"] = {
                "en": [
                    {"label": district, "value": district} for district in districts
                ],
                "hi": [
                    {"label": district, "value": district} for district in districts
                ],
            }

        # Update school field with dependant mapping
        school_field = _find_field_by_key(attributes, "school_name")
        if school_field:
            school_field["dependantFieldMapping"] = district_school_mapping

        logger.info(
            f"Enhanced district->school mapping with {len(districts)} districts"
        )

    except Exception as e:
        logger.error(f"Error enhancing district-school mapping: {e}")


def _enhance_with_district_block_school_mapping(
    attributes: Dict[str, Any], auth_group: str, state: str
):
    """Enhance form with district -> block -> school mapping."""
    try:
        # Get schools data for this state
        response = requests.get(
            school_db_url, params={"state": state}, headers=db_request_token()
        )

        if not is_response_valid(response):
            logger.error(f"Failed to fetch schools data for state: {state}")
            return

        schools_data = response.json()
        if not isinstance(schools_data, list):
            schools_data = [schools_data]

        # Build mappings
        districts = set()
        district_block_mapping = {}
        block_school_mapping = {}

        for school in schools_data:
            district = school.get("district")
            block = school.get("block_name")
            school_name = school.get("name")

            if not district or not school_name:
                continue

            districts.add(district)

            # Build district -> blocks mapping
            if district not in district_block_mapping:
                district_block_mapping[district] = {"en": [], "hi": []}

            if block:
                if block not in district_block_mapping[district]["en"]:
                    district_block_mapping[district]["en"].append(block)
                    district_block_mapping[district]["hi"].append(block)

                # Build block -> schools mapping
                if block not in block_school_mapping:
                    block_school_mapping[block] = {"en": [], "hi": []}

                block_school_mapping[block]["en"].append(school_name)
                block_school_mapping[block]["hi"].append(school_name)

        # Sort data
        districts = sorted(list(districts))
        for district_data in district_block_mapping.values():
            district_data["en"].sort()
            district_data["hi"].sort()
        for block_data in block_school_mapping.values():
            block_data["en"].sort()
            block_data["hi"].sort()

        # Update district field options
        district_field = _find_field_by_key(attributes, "district")
        if district_field:
            district_field["options"] = {
                "en": [
                    {"label": district, "value": district} for district in districts
                ],
                "hi": [
                    {"label": district, "value": district} for district in districts
                ],
            }

        # Update block field with dependant mapping
        block_field = _find_field_by_key(attributes, "block_name")
        if block_field:
            block_field["dependantFieldMapping"] = district_block_mapping

        # Update school field with dependant mapping
        school_field = _find_field_by_key(attributes, "school_name")
        if school_field:
            school_field["dependantFieldMapping"] = block_school_mapping

        logger.info(
            f"Enhanced district->block->school mapping with {len(districts)} districts"
        )

    except Exception as e:
        logger.error(f"Error enhancing district-block-school mapping: {e}")


def _enhance_with_colleges(attributes: Dict[str, Any]):
    """Enhance form with college options using school service."""
    try:
        from services.school_service import get_colleges_list

        colleges_data = get_colleges_list()
        if not colleges_data or "colleges" not in colleges_data:
            logger.error("Failed to get colleges data from school service")
            return

        colleges = colleges_data["colleges"]

        college_field = _find_field_by_key(attributes, "college")
        if college_field:
            college_field["options"] = {
                "en": [{"label": college, "value": college} for college in colleges],
                "hi": [{"label": college, "value": college} for college in colleges],
            }

        logger.info(f"Enhanced college options with {len(colleges)} colleges")

    except Exception as e:
        logger.error(f"Error enhancing college options: {e}")


def _enhance_with_states(attributes: Dict[str, Any]):
    """Enhance form with state options using school service."""
    try:
        from services.school_service import get_states_list

        states_data = get_states_list()
        if not states_data or "states" not in states_data:
            logger.error("Failed to get states data from school service")
            return

        states = states_data["states"]

        state_field = _find_field_by_key(attributes, "state")
        if state_field:
            state_field["options"] = {
                "en": [{"label": state, "value": state} for state in states],
                "hi": [{"label": state, "value": state} for state in states],
            }

        logger.info(f"Enhanced state options with {len(states)} states")

    except Exception as e:
        logger.error(f"Error enhancing state options: {e}")
