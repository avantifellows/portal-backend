from fastapi import APIRouter, Request
import requests
from routes import form_db_url
from services.form_service import get_form_schema_by_id
from services.student_service import get_student_by_id
from mapping import FORM_SCHEMA_QUERY_PARAMS, USER_QUERY_PARAMS, STUDENT_QUERY_PARAMS
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    safe_get_first_item,
)
import logging

router = APIRouter(prefix="/form-schema", tags=["Form"])

logger = logging.getLogger(__name__)


def is_user_attribute_empty(field, student_data):
    return field["key"] in USER_QUERY_PARAMS and (
        student_data["user"][field["key"]] is None
        or student_data["user"][field["key"]] == ""
    )


def is_student_attribute_empty(field, student_data):
    key = field["key"]
    # Special handling for primary_contact attribute with sub-fields for guardians and parents
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

    if key == "primary_contact" or key in guardian_keys or key in parent_keys:
        return any(
            key not in student_data
            or student_data[key] == ""
            or student_data[key] is None
            for key in guardian_keys
        ) and any(
            key not in student_data
            or student_data[key] == ""
            or student_data[key] is None
            for key in parent_keys
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
    returned_form_schema, total_number_of_fields, number_of_fields_left, form_attributes
):
    returned_form_schema[total_number_of_fields - number_of_fields_left] = [
        x for x in list(form_attributes.values()) if x["key"] == "state"
    ][0]
    number_of_fields_left -= 1
    return (returned_form_schema, number_of_fields_left)


def district_in_returned_form_schema_data(
    returned_form_schema,
    total_number_of_fields,
    number_of_fields_left,
    form_attributes,
    student_data,
):
    district_form_field = [
        x for x in list(form_attributes.values()) if x["key"] == "district"
    ][0]
    district_form_field["options"] = district_form_field["dependantFieldMapping"][
        student_data["user"]["state"]
    ]
    district_form_field["dependant"] = False

    returned_form_schema[
        total_number_of_fields - number_of_fields_left
    ] = district_form_field
    number_of_fields_left -= 1
    return (returned_form_schema, number_of_fields_left)


def school_name_in_returned_form_schema_data(
    returned_form_schema,
    total_number_of_fields,
    number_of_fields_left,
    form_attributes,
    student_data,
):
    school_form_field = [
        x for x in list(form_attributes.values()) if x["key"] == "school_name"
    ][0]
    school_form_field["options"] = school_form_field["dependantFieldMapping"][
        student_data["user"]["district"]
    ]
    school_form_field["dependant"] = False

    returned_form_schema[
        total_number_of_fields - number_of_fields_left
    ] = school_form_field
    number_of_fields_left -= 1
    return (returned_form_schema, number_of_fields_left)


def is_field_already_in_schema(field, schema):
    return field["key"] in [value["key"] for value in list(schema.values())]


def build_returned_form_schema_data(
    returned_form_schema, field, number_of_fields_in_form_schema
):
    if not is_field_already_in_schema(field, returned_form_schema):
        returned_form_schema[number_of_fields_in_form_schema] = field
        number_of_fields_in_form_schema += 1
    return (returned_form_schema, number_of_fields_in_form_schema)


def is_user_or_student_attribute_empty_then_build_schema(
    form_schema, number_of_fields_in_form_schema, field, data
):
    return (
        build_returned_form_schema_data(
            form_schema, field, number_of_fields_in_form_schema
        )
        if is_user_attribute_empty(field, data)
        or is_student_attribute_empty(field, data)
        else (form_schema, number_of_fields_in_form_schema)
    )


def find_dependant_parent(fields, priority, dependent_hierarchy, data):
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


def find_children_fields(fields, parent_field):
    children_fields = []
    for field in fields:
        if fields[field]["dependantField"] == parent_field["key"] or (
            len(fields[field]["showBasedOn"]) > 0
            and fields[field]["showBasedOn"].split("==")[0] == parent_field["key"]
        ):
            children_fields.append(int(field))

    return children_fields


@router.get("/")
def get_form_schema(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, FORM_SCHEMA_QUERY_PARAMS
    )

    logger.info(f"Fetching form schema with params: {query_params}")

    response = requests.get(
        form_db_url, params=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "Form API could not fetch the data!"):
        # Use safe_get_first_item instead of direct array access
        form_data = safe_get_first_item(response.json(), "Form does not exist!")
        logger.info("Successfully retrieved form schema data")
        return form_data


@router.get("/student")
async def get_student_fields(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        ["number_of_fields_in_popup_form", "form_id", "student_id"],
    )

    form = get_form_schema_by_id(query_params["form_id"])

    student_response = get_student_by_id(query_params["student_id"])
    student_data = student_response[0] if student_response and len(student_response) > 0 else {}

    # get the priorities for all fields and sort them
    priority_order = sorted([eval(i) for i in form["attributes"].keys()])

    fields = form["attributes"]

    total_number_of_fields = int(query_params["number_of_fields_in_popup_form"])

    number_of_fields_in_form_schema = 0

    returned_form_schema = {}

    for priority in priority_order:
        if number_of_fields_in_form_schema <= total_number_of_fields:
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

            # else:

            #         (
            #         returned_form_schema,
            #         number_of_fields_in_form_schema,
            #     ) = is_user_or_student_attribute_empty_then_build_schema(
            #         returned_form_schema,
            #         number_of_fields_in_form_schema,
            #         fields[str(priority)],
            #         student_data,
            #     )

    return returned_form_schema
