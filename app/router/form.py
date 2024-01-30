from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from router import student, routes, enrollment_record, student_exam_record
from request import build_request
import helpers
import mapping
from helpers import db_request_token

router = APIRouter(prefix="/form-schema", tags=["Form"])

def build_returned_form_schema_data(form_schema, number_of_fields_in_form_schema, set_of_fields, priority):
    """
    Builds and returns updated form schema data.

    Parameters:
    - form_schema (dict): The existing form schema data.
    - number_of_fields_in_form_schema (int): The current count of fields in the form schema.
    - set_of_fields (dict): A dictionary containing fields with priorities.
    - priority (int): The priority of the field to be added.

    Returns:
    - tuple: A tuple containing the updated form schema and the incremented count of fields.
    """
    form_schema[number_of_fields_in_form_schema] = set_of_fields[str(priority)]
    number_of_fields_in_form_schema += 1
    return (form_schema, number_of_fields_in_form_schema)


def state_in_returned_form_schema_data(form_schema, number_of_fields_in_form_schema, set_of_fields):
    """
    Adds the 'state' field data to the returned form schema.

    Args:
    - form_schema (dict): The existing form schema data.
    - number_of_fields_in_form_schema (int): The current count of fields in the form schema.
    - set_of_fields (dict): A dictionary containing fields.

    Returns:
    - tuple: A tuple containing the updated form schema and the incremented count of fields.
    """
    form_schema[number_of_fields_in_form_schema] = [
        x for x in list(set_of_fields.values()) if x["key"] == "state"
    ][0]
    number_of_fields_in_form_schema += 1
    return (form_schema, number_of_fields_in_form_schema)


def district_in_returned_form_schema_data(form_schema, number_of_fields_in_form_schema, set_of_fields, student_data):
    """
    Adds the 'district' field data to the returned form schema.

    Args:
    - form_schema (dict): The existing form schema data.
    - number_of_fields_in_form_schema (int): The current count of fields in the form schema.
    - set_of_fields (dict): A dictionary containing fields.
    - student_data (dict): Data related to the student, including the 'state' information, which will be used to get respective 'state' values.

    Returns:
    - tuple: A tuple containing the updated form schema and the incremented count of fields.
    """
    district_form_field = [
        x for x in list(set_of_fields.values()) if x["key"] == "district"
    ][0]
    district_form_field["options"] = district_form_field["dependantFieldMapping"][
        student_data["user"]["state"]
    ]
    district_form_field["dependant"] = False

    form_schema[number_of_fields_in_form_schema] = district_form_field
    number_of_fields_in_form_schema += 1
    return (form_schema, number_of_fields_in_form_schema)


def school_name_in_returned_form_schema_data(form_schema, number_of_fields_in_form_schema, set_of_fields, student_data):
    """
    Adds the 'school' field data to the returned form schema.

    Args:
    - form_schema (dict): The existing form schema data.
    - number_of_fields_in_form_schema (int): The current count of fields in the form schema.
    - set_of_fields (dict): A dictionary containing fields.
    - student_data (dict): Data related to the student, including the 'district' information, which will be used to get respective 'school' values.

    Returns:
    - tuple: A tuple containing the updated form schema and the incremented count of fields.
    """
    school_form_field = [
        x for x in list(set_of_fields.values()) if x["key"] == "school_name"
    ][0]
    school_form_field["options"] = school_form_field["dependantFieldMapping"][
        student_data["user"]["district"]
    ]
    school_form_field["dependant"] = False

    form_schema[number_of_fields_in_form_schema] = school_form_field
    number_of_fields_in_form_schema += 1
    return (form_schema, number_of_fields_in_form_schema)


def is_user_attribute_empty(set_of_fields, priority, student_data):
    """
    Checks if a user attribute is empty in the student data based on the given form attributes.

    Args:
    - set_of_fields (dict): The set of form fields.
    - priority (int): The priority of the field.
    - student_data (dict): Data related to the student.

    Returns:
    - bool: True if the user attribute is empty, False otherwise.
    """
    return (set_of_fields[str(priority)]["key"] in mapping.USER_QUERY_PARAMS and (student_data["user"][set_of_fields[str(priority)]["key"]] is None or student_data["user"][set_of_fields[str(priority)]["key"]] == ''))


def is_student_attribute_empty(set_of_fields, priority, student_data):
    """
    Checks if a student attribute is empty in the student data based on the given set of fields.

    Args:
    - set_of_fields (dict): The set of fields representing the form.
    - priority (int): The priority of the field.
    - student_data (dict): Data related to the student.

    Returns:
    - bool: True if the student attribute is empty, False otherwise.
    """
    key = set_of_fields[str(priority)]["key"]
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
        return (
            all(key not in student_data or student_data[key] == "" or student_data[key] is None for key in guardian_keys)
            and all(key not in student_data or student_data[key] == "" or student_data[key] is None for key in parent_keys)
        )
    return key in mapping.STUDENT_QUERY_PARAMS and (key not in student_data or student_data[key] is None or student_data[key] == '')


def is_user_or_student_attribute_empty_then_build_schema(form_schema, number_of_fields_in_form_schema, set_of_fields, priority, data):
    """
    Checks if either user or student attribute is empty, and builds the form schema accordingly.

    Args:
    - set_of_fields (dict): The set of fields.
    - priority (int): The priority of the field.
    - data (dict): Data related to the user or student.
    - form_schema (dict): The existing form schema data.
    - number_of_fields_in_form_schema (int): The current count of fields in the form schema.

    Returns:
    - tuple: A tuple containing the updated form schema and the incremented count of fields.
    """

    return (
        build_returned_form_schema_data(form_schema, number_of_fields_in_form_schema, set_of_fields, priority)
        if is_user_attribute_empty(set_of_fields, priority, data) or is_student_attribute_empty(set_of_fields, priority, data)
        else (form_schema, number_of_fields_in_form_schema)
    )


def is_enrollment_record_attribute_empty(set_of_fields, priority, enrollment_data):
    """
    Checks if a enrollment record attribute is empty in the enrollment data based on the given form attributes.

    Args:
    - set_of_fields (dict): The set of form fields.
    - priority (int): The priority of the field.
    - enrollment_data (dict): Data related to the student.

    Returns:
    - bool: True if the enrollment record attribute is empty, False otherwise.
    """
    return (set_of_fields[str(priority)]["key"] == 'school_name' and enrollment_data["school_id"] is None or enrollment_data["school_id"] == '') or ((set_of_fields[str(priority)]["key"] in mapping.ENROLLMENT_RECORD_PARAMS and set_of_fields[str(priority)]["key"] != 'school_name' and set_of_fields[str(priority)]["key"] != "student_id" and  (enrollment_data[set_of_fields[str(priority)]["key"]] is None or enrollment_data[set_of_fields[str(priority)]["key"]] == '')))


def find_dependant_parent(fields, priority, dependent_hierarchy, data):
    parent_field_priority = [key for key, value in list(fields.items()) if value["key"] == fields[str(priority)]["dependantField"]]

    if len(parent_field_priority) == 1:
        dependent_hierarchy.append(int(parent_field_priority[0]))
        find_dependant_parent(fields, parent_field_priority[0], dependent_hierarchy, data)


def is_enrollment_record_attribute_empty_then_build_schema(form_schema, number_of_fields_in_form_schema, set_of_fields, priority, data):
    if is_enrollment_record_attribute_empty(set_of_fields, priority, data):
        if set_of_fields[str(priority)]["dependant"]:
            dependent_hierarchy= [priority]
            find_dependant_parent(set_of_fields, priority,dependent_hierarchy, data )

            for dependant_field_priority in sorted(dependent_hierarchy):
                (form_schema,number_of_fields_in_form_schema) = build_returned_form_schema_data(form_schema,number_of_fields_in_form_schema,set_of_fields,dependant_field_priority)
        else:
            (form_schema,number_of_fields_in_form_schema) = build_returned_form_schema_data(form_schema,number_of_fields_in_form_schema,set_of_fields,priority)

    return (form_schema, number_of_fields_in_form_schema)


def is_student_exam_record_attribute_empty(set_of_fields, priority, student_exam_record_data):
    return (set_of_fields[str(priority)]["key"] in mapping.STUDENT_EXAM_RECORD_QUERY_PARAMS and set_of_fields[str(priority)]["key"] != "student_id" and  (student_exam_record_data[set_of_fields[str(priority)]["key"]] is None or student_exam_record_data[set_of_fields[str(priority)]["key"]] == ''))


def is_student_exam_record_attribute_empty_then_build_schema(form_schema, number_of_fields_in_form_schema, set_of_fields, priority, data):
    if set_of_fields[str(priority)]["key"] in mapping.STUDENT_EXAM_RECORD_QUERY_PARAMS:
        if len(data) > 0:
            for record in data:
                if is_student_exam_record_attribute_empty(set_of_fields, priority, record):
                    if set_of_fields[str(priority)]["dependant"]:
                        dependent_hierarchy= [priority]
                        find_dependant_parent(set_of_fields, priority,dependent_hierarchy )

                        for dependant_field_priority in sorted(dependent_hierarchy):
                            (form_schema,number_of_fields_in_form_schema) = build_returned_form_schema_data(form_schema,number_of_fields_in_form_schema,set_of_fields,dependant_field_priority)
                        return (form_schema,number_of_fields_in_form_schema)


        return build_returned_form_schema_data(form_schema,number_of_fields_in_form_schema,set_of_fields,priority)
    return (form_schema, number_of_fields_in_form_schema)

@router.get("/")
def get_form_schema(request: Request):
    """
    This API returns a form schema when an ID or a name is given.

    Returns:
    list: form schema data if ID/name is a match, otherwise 404

    Example:
    > $BASE_URL/form_schema/?form_schema_id=1234
    returns [{form_schema_data_of_id_1234}]

    """
    query_params = helpers.validate_and_build_query_params(
        request.query_params, ["id", "name"]
    )

    response = requests.get(
        routes.form_db_url, params=query_params, headers=db_request_token()
    )
    if helpers.is_response_valid(response, "Form API could not fetch the data!"):
        return helpers.is_response_empty(response.json(), False, "Form does not exist!")


@router.get("/student")
async def get_student_fields(request: Request):
    query_params = helpers.validate_and_build_query_params(
        request.query_params, ["number_of_fields_in_pop_form", "group", "student_id" ]
    )

    # get the field ordering for a particular group
    form = get_form_schema(
        build_request(
            query_params={"name": mapping.FORM_GROUP_MAPPING[query_params["group"]]}
        )
    )[0]


    # get student and user data for the student ID that is requesting for profile completion
    student_data = student.get_students(
        build_request(query_params={"student_id": query_params["student_id"]})
    )[0]


    # get enrollment data for the student
    enrollment_record_data = enrollment_record.get_enrollment_record(
        build_request(query_params={"student_id": student_data["id"]})
    )[0]


    # get exam data for the student
    student_exam_record_data = student_exam_record.get_student_exam_record(
        build_request(query_params={"student_id": student_data["id"]})
    )

    if len(student_exam_record_data) == 0:
        student_exam_record_data = {}


    complete_student_data = {**student_data, **student_data['user'], ** enrollment_record_data, **student_exam_record_data}

    # get the priorities for all fields and sort them
    set_numbers = sorted([eval(i) for i in form["attributes"].keys()])

    # get the form attributes
    fields = form["attributes"]

    # number of fields to sent back to the student
    total_number_of_fields =  int(query_params["number_of_fields_in_pop_form"])

    number_of_fields_in_form_schema = 0

    returned_form_schema = {}
    for number in set_numbers:
        if number_of_fields_in_form_schema <= total_number_of_fields:
            priority_order = sorted([eval(i) for i in fields[str(number)].keys()])

            for priority in sorted(priority_order):


                (returned_form_schema,number_of_fields_in_form_schema) = is_user_or_student_attribute_empty_then_build_schema(returned_form_schema, number_of_fields_in_form_schema, fields[str(number)], priority, student_data)
                (returned_form_schema,number_of_fields_in_form_schema) = is_enrollment_record_attribute_empty_then_build_schema(returned_form_schema, number_of_fields_in_form_schema, fields[str(number)], priority, enrollment_record_data)
               # (returned_form_schema,number_of_fields_in_form_schema) = is_student_exam_record_attribute_empty_then_build_schema(returned_form_schema, number_of_fields_in_form_schema, fields[str(number)], priority, complete_student_data)

    return returned_form_schema

