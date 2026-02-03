"""Form service for business logic without HTTP dependencies."""

import requests
from typing import Dict, Any, Optional
from logger_config import get_logger
from routes import form_db_url
from helpers import db_request_token, is_response_valid, safe_get_first_item
from mapping import (
    FORM_SCHEMA_QUERY_PARAMS,
    USER_QUERY_PARAMS,
    STUDENT_QUERY_PARAMS,
    authgroup_state_mapping,
)
from services.school_service import (
    get_states_list,
    get_colleges_list,
    get_dependant_field_mapping_for_auth_group,
)
from services.student_service import get_student_by_id
from services.user_service import get_user_by_id

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


def get_form_schema_with_enhancement(
    auth_group: Optional[str] = None, **params
) -> Optional[Dict[str, Any]]:
    """Get form schema with optional dynamic data enhancement."""
    form_data = get_form_schema(**params)

    if form_data and auth_group:
        form_data = enhance_form_schema_with_dynamic_data(form_data, auth_group)
        logger.info("Successfully retrieved and enhanced form schema")

    return form_data


def enhance_form_schema_with_dynamic_data(
    form_data: Dict[str, Any], auth_group: str
) -> Dict[str, Any]:
    """
    Enhance form schema with dynamic data from database.
    This replaces frontend form enhancement logic for better performance and reliability.
    """
    if not form_data or not form_data.get("attributes") or not auth_group:
        return form_data

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
    needs_colleges = _has_field(attributes, "college_name")
    needs_states = _has_field(attributes, "state")

    # For district/school mappings, we need the auth_group to be in the mapping
    if auth_group in authgroup_state_mapping:
        state = authgroup_state_mapping[auth_group]

        if needs_district_block_school:
            _enhance_with_district_block_school_mapping(attributes, auth_group, state)
        elif needs_district_school:
            _enhance_with_district_school_mapping(attributes, auth_group, state)
    else:
        logger.warning(
            f"Unknown auth_group for school/district enhancement: {auth_group}"
        )

    # These enhancements don't require auth_group mapping
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
    attributes: Dict[str, Any],
    auth_group: str,
    state: str,  # state kept for API compatibility
):
    """Enhance form with district -> school mapping."""
    try:
        # Get mapping data from school service
        mapping_data = get_dependant_field_mapping_for_auth_group(
            auth_group, include_blocks=False
        )

        if "error" in mapping_data:
            logger.error(
                f"Failed to get district-school mapping: {mapping_data['error']}"
            )
            return

        district_school_mapping = mapping_data["district_school_mapping"]
        districts = sorted(list(district_school_mapping.keys()))

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
    attributes: Dict[str, Any],
    auth_group: str,
    state: str,  # state kept for API compatibility
):
    """Enhance form with district -> block -> school mapping."""
    try:
        # Get mapping data from school service
        mapping_data = get_dependant_field_mapping_for_auth_group(
            auth_group, include_blocks=True
        )

        if "error" in mapping_data:
            logger.error(
                f"Failed to get district-block-school mapping: {mapping_data['error']}"
            )
            return

        district_block_mapping = mapping_data["district_block_mapping"]
        block_school_mapping = mapping_data["block_school_mapping"]
        districts = sorted(list(district_block_mapping.keys()))

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
        colleges_data = get_colleges_list()
        if not colleges_data or "colleges" not in colleges_data:
            logger.error("Failed to get colleges data from school service")
            return

        colleges = colleges_data["colleges"]

        college_field = _find_field_by_key(attributes, "college_name")
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


def is_user_attribute_empty(
    field: Dict[str, Any], student_data: Dict[str, Any]
) -> bool:
    """Check if user attribute is empty."""

    if field["key"] not in USER_QUERY_PARAMS:
        return False

    user_data = student_data.get("user") if isinstance(student_data, dict) else None
    if not user_data:
        return True

    return user_data.get(field["key"]) in (None, "")


def is_student_attribute_empty(
    field: Dict[str, Any], student_data: Dict[str, Any]
) -> bool:
    """Check if student attribute is empty."""

    key = field["key"]
    guardian_keys = [
        "guardian_name",
        "guardian_relation",
        "guardian_phone",
        "guardian_education_level",
        "guardian_profession",
    ]
    parent_keys = [
        "father_name",
        "father_phone",
        "father_profession",
        "father_education_level",
        "mother_name",
        "mother_phone",
        "mother_profession",
        "mother_education_level",
    ]

    if key == "primary_contact":
        return any(
            guardian_key not in student_data
            or student_data[guardian_key] == ""
            or student_data[guardian_key] is None
            for guardian_key in guardian_keys
        ) and any(
            parent_key not in student_data
            or student_data[parent_key] == ""
            or student_data[parent_key] is None
            for parent_key in parent_keys
        )
    elif key in guardian_keys or key in parent_keys:
        return (
            key not in student_data
            or student_data[key] == ""
            or student_data[key] is None
        )

    if key == "grade":
        return (
            "grade_id" not in student_data
            or student_data["grade_id"] is None
            or student_data["grade_id"] == ""
        )
    return key in STUDENT_QUERY_PARAMS and (
        key not in student_data or student_data[key] is None or student_data[key] == ""
    )


def state_in_returned_form_schema_data(
    returned_form_schema: Dict[int, Any],
    total_number_of_fields: int,
    number_of_fields_left: int,
    form_attributes: Dict[str, Any],
) -> tuple:
    """Add state field to returned form schema."""
    returned_form_schema[total_number_of_fields - number_of_fields_left] = [
        x for x in list(form_attributes.values()) if x["key"] == "state"
    ][0]
    number_of_fields_left -= 1
    return (returned_form_schema, number_of_fields_left)


def district_in_returned_form_schema_data(
    returned_form_schema: Dict[int, Any],
    total_number_of_fields: int,
    number_of_fields_left: int,
    form_attributes: Dict[str, Any],
    student_data: Dict[str, Any],
) -> tuple:
    """Add district field to returned form schema."""
    district_form_field = [
        x for x in list(form_attributes.values()) if x["key"] == "district"
    ][0]
    user_data = student_data.get("user") if isinstance(student_data, dict) else {}
    state = user_data.get("state") if isinstance(user_data, dict) else None
    if (
        state
        and "dependantFieldMapping" in district_form_field
        and state in district_form_field["dependantFieldMapping"]
    ):
        district_form_field["options"] = district_form_field["dependantFieldMapping"][
            state
        ]
        district_form_field["dependant"] = False

    returned_form_schema[total_number_of_fields - number_of_fields_left] = (
        district_form_field
    )
    number_of_fields_left -= 1
    return (returned_form_schema, number_of_fields_left)


def school_name_in_returned_form_schema_data(
    returned_form_schema: Dict[int, Any],
    total_number_of_fields: int,
    number_of_fields_left: int,
    form_attributes: Dict[str, Any],
    student_data: Dict[str, Any],
) -> tuple:
    """Add school name field to returned form schema."""
    school_form_field = [
        x for x in list(form_attributes.values()) if x["key"] == "school_name"
    ][0]
    user_data = student_data.get("user") if isinstance(student_data, dict) else {}
    district = user_data.get("district") if isinstance(user_data, dict) else None
    if (
        district
        and "dependantFieldMapping" in school_form_field
        and district in school_form_field["dependantFieldMapping"]
    ):
        school_form_field["options"] = school_form_field["dependantFieldMapping"][
            district
        ]
        school_form_field["dependant"] = False

    returned_form_schema[total_number_of_fields - number_of_fields_left] = (
        school_form_field
    )
    number_of_fields_left -= 1
    return (returned_form_schema, number_of_fields_left)


def is_field_already_in_schema(field: Dict[str, Any], schema: Dict[int, Any]) -> bool:
    """Check if field is already in schema."""
    return field["key"] in [value["key"] for value in list(schema.values())]


def build_returned_form_schema_data(
    returned_form_schema: Dict[int, Any],
    field: Dict[str, Any],
    number_of_fields_in_form_schema: int,
) -> tuple:
    """Build returned form schema data."""
    if not is_field_already_in_schema(field, returned_form_schema):
        returned_form_schema[number_of_fields_in_form_schema] = field
        number_of_fields_in_form_schema += 1
    return (returned_form_schema, number_of_fields_in_form_schema)


def is_user_or_student_attribute_empty_then_build_schema(
    form_schema: Dict[int, Any],
    number_of_fields_in_form_schema: int,
    field: Dict[str, Any],
    data: Dict[str, Any],
) -> tuple:
    """Check if user or student attribute is empty then build schema."""
    return (
        build_returned_form_schema_data(
            form_schema, field, number_of_fields_in_form_schema
        )
        if is_user_attribute_empty(field, data)
        or is_student_attribute_empty(field, data)
        else (form_schema, number_of_fields_in_form_schema)
    )


def find_dependant_parent(
    fields: Dict[str, Any],
    priority: int,
    dependent_hierarchy: list,
    data: Dict[str, Any],
) -> list:
    """Find dependant parent field."""
    parent_field_priority = [
        key
        for key, value in list(fields.items())
        if value["key"] == fields[str(priority)]["dependantField"]
    ]

    if len(parent_field_priority) == 1:
        dependent_hierarchy.append(int(parent_field_priority[0]))
        find_dependant_parent(
            fields, parent_field_priority[0], dependent_hierarchy, data
        )

    return dependent_hierarchy


def find_children_fields(fields: Dict[str, Any], parent_field: Dict[str, Any]) -> list:
    """Find children fields."""
    children_fields = []
    for field in fields:
        if fields[field]["dependantField"] == parent_field["key"] or (
            len(fields[field]["showBasedOn"]) > 0
            and fields[field]["showBasedOn"].split("==")[0] == parent_field["key"]
        ):
            children_fields.append(int(field))

    return children_fields


def get_student_fields_for_form(
    form_id: str, student_id: str, number_of_fields_in_popup_form: int
) -> Dict[int, Any]:
    """Get student fields for form"""

    form = get_form_schema_by_id(form_id)
    if not form:
        logger.error(f"Form not found with ID: {form_id}")
        return {}

    student_response = get_student_by_id(student_id)
    student_data = (
        student_response[0] if student_response and len(student_response) > 0 else {}
    )

    if isinstance(student_data, dict) and not isinstance(
        student_data.get("user"), dict
    ):
        user_lookup = None
        user_id = student_data.get("user_id")
        if user_id:
            user_lookup = get_user_by_id(user_id)

        if user_lookup:
            if isinstance(user_lookup, list):
                user_lookup = user_lookup[0]
            if isinstance(user_lookup, dict):
                student_data["user"] = user_lookup

    priority_order = sorted([eval(i) for i in form["attributes"].keys()])
    fields = form["attributes"]
    total_number_of_fields = int(number_of_fields_in_popup_form)
    number_of_fields_in_form_schema = 0
    returned_form_schema = {}

    for priority in priority_order:
        if number_of_fields_in_form_schema < total_number_of_fields:
            children_fields = find_children_fields(fields, fields[str(priority)])
            children_fields.append(priority)

            for child_field in sorted(children_fields):
                (
                    returned_form_schema,
                    number_of_fields_in_form_schema,
                ) = is_user_or_student_attribute_empty_then_build_schema(
                    returned_form_schema,
                    number_of_fields_in_form_schema,
                    fields[str(child_field)],
                    student_data,
                )

    return returned_form_schema
