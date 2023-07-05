from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from router import student, routes, enrollment_record
from request import build_request
import helpers
import mapping

router = APIRouter(prefix="/form-schema", tags=["Form"])


def is_user_attribute_empty(form_attributes, priority, student_data):
    return (
        form_attributes[str(priority)]["key"] in mapping.USER_QUERY_PARAMS
        and student_data["user"][form_attributes[str(priority)]["key"]] is None
    )


def is_student_attribute_empty(form_attributes, priority, student_data):
    return (
        form_attributes[str(priority)]["key"] in mapping.STUDENT_QUERY_PARAMS
        and student_data[form_attributes[str(priority)]["key"]] is None
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
    returned_form_schema,
    total_number_of_fields,
    number_of_fields_left,
    form_attributes,
    priority,
):
    returned_form_schema[
        total_number_of_fields - number_of_fields_left
    ] = form_attributes[str(priority)]
    number_of_fields_left -= 1
    return (returned_form_schema, number_of_fields_left)


@router.get("/")
def get_form_schema(request: Request):
    """
    This API returns a form schema when an ID is given

    Returns:
    list: form schema data if ID is a match, otherwise 404

    Example:
    > $BASE_URL/form_schema/?form_schema_id=1234
    returns [{form_schema_data_of_id_1234}]

    """
    query_params = helpers.validate_and_build_query_params(
        request.query_params, ["id", "name"]
    )
    response = requests.get(routes.form_db_url, params=query_params)
    if helpers.is_response_valid(response, "Form API could not fetch the data!"):
        return helpers.is_response_empty(response.json(), "Form does not exist!")


@router.get("/student")
async def get_student_fields(request: Request):
    query_params = helpers.validate_and_build_query_params(
        request.query_params, ["number_of_fields", "group", "student_id"]
    )

    # get the field ordering for a particular group
    form = get_form_schema(
        build_request(
            query_params={"name": mapping.FORM_GROUP_MAPPING[query_params["group"]]}
        )
    )
    form = form[0]

    # get student and user data for the student ID that is requesting for profile completion
    # ASSUMPTION : student_id is valid and exists because only valid students will reach profile completion
    student_data = student.get_students(
        build_request(query_params={"student_id": query_params["student_id"]})
    )

    if student_data:

        student_data = student_data[0]

        # get enrollment data for the student
        enrollment_record_data = enrollment_record.get_enrollment_record(
            build_request(query_params={"student_id": student_data["id"]})
        )

        # get the priorities for all fields and sort them
        priority_order = sorted([eval(i) for i in form["attributes"].keys()])

        # get the form attributes
        form_attributes = form["attributes"]

        # number of fields to sent back to the student
        total_number_of_fields = number_of_fields_left = int(
            query_params["number_of_fields"]
        )

        returned_form_schema = {}

        for priority in priority_order:

            if number_of_fields_left > 0:

                if is_user_attribute_empty(
                    form_attributes, priority, student_data
                ) or is_student_attribute_empty(
                    form_attributes, priority, student_data
                ):

                    (
                        returned_form_schema,
                        number_of_fields_left,
                    ) = build_returned_form_schema_data(
                        returned_form_schema,
                        total_number_of_fields,
                        number_of_fields_left,
                        form_attributes,
                        priority,
                    )

                elif (
                    form_attributes[str(priority)]["key"]
                    in mapping.ENROLLMENT_RECORD_PARAMS
                    and form_attributes[str(priority)]["key"] != "student_id"
                ):

                    if form_attributes[str(priority)]["key"] != "school_name":
                        if (
                            enrollment_record_data == []
                            or enrollment_record_data[
                                form_attributes[str(priority)]["key"]
                            ]
                            is None
                        ):
                            (
                                returned_form_schema,
                                number_of_fields_left,
                            ) = build_returned_form_schema_data(
                                returned_form_schema,
                                total_number_of_fields,
                                number_of_fields_left,
                                form_attributes,
                                priority,
                            )
                    else:
                        if enrollment_record_data == []:
                            if student_data["user"]["state"]:
                                if student_data["user"]["district"]:

                                    (
                                        returned_form_schema,
                                        number_of_fields_left,
                                    ) = school_name_in_returned_form_schema_data(
                                        returned_form_schema,
                                        total_number_of_fields,
                                        number_of_fields_left,
                                        form_attributes,
                                        student_data,
                                    )

                                else:
                                    (
                                        returned_form_schema,
                                        number_of_fields_left,
                                    ) = district_in_returned_form_schema_data(
                                        returned_form_schema,
                                        total_number_of_fields,
                                        number_of_fields_left,
                                        form_attributes,
                                        student_data,
                                    )
                            else:
                                (
                                    returned_form_schema,
                                    number_of_fields_left,
                                ) = state_in_returned_form_schema_data(
                                    returned_form_schema,
                                    total_number_of_fields,
                                    number_of_fields_left,
                                    form_attributes,
                                )
                        else:
                            enrollment_record_data = enrollment_record_data[0]
                            if enrollment_record_data["school_id"] is None:
                                if student_data["user"]["district"] is None:
                                    if student_data["user"]["state"] is None:
                                        (
                                            returned_form_schema,
                                            number_of_fields_left,
                                        ) = state_in_returned_form_schema_data(
                                            returned_form_schema,
                                            total_number_of_fields,
                                            number_of_fields_left,
                                            form_attributes,
                                        )
                                    else:
                                        (
                                            returned_form_schema,
                                            number_of_fields_left,
                                        ) = district_in_returned_form_schema_data(
                                            returned_form_schema,
                                            total_number_of_fields,
                                            number_of_fields_left,
                                            form_attributes,
                                            student_data,
                                        )
                                else:
                                    (
                                        returned_form_schema,
                                        number_of_fields_left,
                                    ) = school_name_in_returned_form_schema_data(
                                        returned_form_schema,
                                        total_number_of_fields,
                                        number_of_fields_left,
                                        form_attributes,
                                        student_data,
                                    )

        return returned_form_schema

    raise HTTPException(status_code=404, detail="Student does not exist!")
