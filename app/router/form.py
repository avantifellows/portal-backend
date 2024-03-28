from fastapi import APIRouter, Request
import requests
from routes import form_db_url
from settings import settings
from router import student, enrollment_record
from request import build_request
from mapping import FORM_SCHEMA_QUERY_PARAMS, USER_QUERY_PARAMS, STUDENT_QUERY_PARAMS
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)

router = APIRouter(prefix="/form-schema", tags=["Form"])


def is_user_attribute_empty(field, student_data):
    return field["key"] in USER_QUERY_PARAMS and (
        student_data["user"][field["key"]] is None
        or student_data["user"][field["key"]] == ""
    )


def is_student_attribute_empty(field, student_data):
    key = field["key"]
    if key == "primary_contact":
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
        return all(
            key not in student_data
            or student_data[key] == ""
            or student_data[key] is None
            for key in guardian_keys
        ) and all(
            key not in student_data
            or student_data[key] == ""
            or student_data[key] is None
            for key in parent_keys
        )
    
    if key == "grade":
        return "grade_id" not in student_data or student_data["grade_id"] is None or student_data["grade_id"] == ""
        
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


def build_returned_form_schema_data(
    returned_form_schema, field, number_of_fields_in_form_schema
):
    returned_form_schema[number_of_fields_in_form_schema] = field
    number_of_fields_in_form_schema += 1
    return (returned_form_schema, number_of_fields_in_form_schema)


def is_user_or_student_attribute_empty_then_build_schema(
    form_schema, number_of_fields_in_form_schema, field, data
):
    print(
        field["key"],
        is_user_attribute_empty(field, data),
        is_student_attribute_empty(field, data),
    )
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


@router.get("/")
def get_form_schema(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params, FORM_SCHEMA_QUERY_PARAMS
    )
    response = requests.get(
        form_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "Form API could not fetch the data!"):
        return is_response_empty(response.json()[0], "True", "Form does not exist!")


@router.get("/student")
async def get_student_fields(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        ["number_of_fields_in_popup_form", "form_id", "student_id"],
    )

    form = get_form_schema(build_request(query_params={"id": query_params["form_id"]}))

    student_data = student.get_students(
        build_request(query_params={"student_id": query_params["student_id"]})
    )[0]

    # get the priorities for all fields and sort them
    priority_order = sorted([eval(i) for i in form["attributes"].keys()])

    fields = form["attributes"]

    total_number_of_fields = int(query_params["number_of_fields_in_popup_form"])

    number_of_fields_in_form_schema = 0

    returned_form_schema = {}

    for priority in priority_order:
        if number_of_fields_in_form_schema <= total_number_of_fields:
            print(fields[str(priority)]["key"])
            (
                returned_form_schema,
                number_of_fields_in_form_schema,
            ) = is_user_or_student_attribute_empty_then_build_schema(
                returned_form_schema,
                number_of_fields_in_form_schema,
                fields[str(priority)],
                student_data,
            )

    return returned_form_schema
