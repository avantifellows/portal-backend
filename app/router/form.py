from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from router import student, routes, enrollment_record
from request import build_request
import helpers
import mapping

router = APIRouter(prefix="/form-schema", tags=["Form"])


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
    return returned_form_schema


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
        request, ["id", "name"]
    )
    response = requests.get(routes.form_db_url, params=query_params)
    if helpers.is_response_valid(response, "Form API could not fetch the data!"):
        return response.json()


@router.get("/student")
async def get_student_fields(request: Request):
    query_params = helpers.validate_and_build_query_params(
        request, ["number_of_fields", "group", "student_id"]
    )

    # get the field ordering for a particular group
    form = get_form_schema(build_request(query_params={"name":mapping.FORM_GROUP_MAPPING[query_params["group"]]}))
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
                print("Priority:", form_attributes[str(priority)]["key"])
                # if the form field is first name of last name, we check if full name exists in the database
                if (
                    (
                        (form_attributes[str(priority)]["key"] == "first_name"
                        or form_attributes[str(priority)]["key"] == "last_name")
                        and student_data["user"]["full_name"] is None
                    )
                    or (
                        form_attributes[str(priority)]["key"]
                        in mapping.USER_QUERY_PARAMS
                        and form_attributes[str(priority)]["key"] != "first_name"
                        and form_attributes[str(priority)]["key"] != "last_name"
                        and student_data["user"][form_attributes[str(priority)]["key"]]
                        is None
                    )
                    or (
                        form_attributes[str(priority)]["key"]
                        in mapping.STUDENT_QUERY_PARAMS
                        and student_data[form_attributes[str(priority)]["key"]] is None
                    )
                ):

                    build_returned_form_schema_data(
                        returned_form_schema,
                        total_number_of_fields,
                        number_of_fields_left,
                        form_attributes,
                        priority,
                    )

                # if the form field is a enrollment record table attribute, we check in the enrollement record table
                elif (
                    form_attributes[str(priority)]["key"]
                    in mapping.ENROLLMENT_RECORD_PARAMS
                    and form_attributes[str(priority)]["key"] != "student_id"
                ):


                    if form_attributes[str(priority)]["key"] != "school_name":
                        print(form_attributes[str(priority)]["key"], enrollment_record_data)
                        if enrollment_record_data == [] or enrollment_record_data[form_attributes[str(priority)]["key"]] is None:
                            build_returned_form_schema_data(
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
                                    returned_form_schema[
                                        total_number_of_fields - number_of_fields_left
                                    ] = [
                                        x
                                        for x in list(form_attributes.values())
                                        if x["key"] == "school_name"
                                    ][
                                        0
                                    ]
                                returned_form_schema[
                                    total_number_of_fields - number_of_fields_left
                                ] = [
                                    x
                                    for x in list(form_attributes.values())
                                    if x["key"] == "district"
                                ][
                                    0
                                ]
                            returned_form_schema[
                                total_number_of_fields - number_of_fields_left
                            ] = [
                                x
                                for x in list(form_attributes.values())
                                if x["key"] == "state"
                            ][
                                0
                            ]
                        else:
                            enrollment_record_data = enrollment_record_data[0]

                            if enrollment_record_data["school_id"] is None:
                                if student_data["user"]["district"] is None:
                                    if student_data["user"]["state"] is None:
                                        returned_form_schema[
                                            total_number_of_fields
                                            - number_of_fields_left
                                        ] = [
                                            x
                                            for x in list(form_attributes.values())
                                            if x["key"] == "state"
                                        ][
                                            0
                                        ]
                                        number_of_fields_left -= 1
                                    else:
                                        returned_form_schema[
                                            total_number_of_fields
                                            - number_of_fields_left
                                        ] = [
                                            x
                                            for x in list(form_attributes.values())
                                            if x["key"] == "district"
                                        ][
                                            0
                                        ]
                                        number_of_fields_left -= 1
                                else:
                                    returned_form_schema[
                                        total_number_of_fields - number_of_fields_left
                                    ] = [
                                        x
                                        for x in list(form_attributes.values())
                                        if x["key"] == "school_name"
                                    ][
                                        0
                                    ]
                                    number_of_fields_left -= 1

        return returned_form_schema

    raise HTTPException(status_code=404, detail="Student does not exist!")
