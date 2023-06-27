from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from router import student
from request import build_request

router = APIRouter(tags=["Form"])
form_db_url = settings.db_url + "/form-schema"
student_db_url = settings.db_url + "/student"
enrollment_record_db_url = settings.db_url + "/enrollment-record"

FORM_GROUP_MAPPING = {"HaryanaStudents": "Haryana_Student_Details"}

STUDENT_QUERY_PARAMS = [
    "student_id",
    "father_name",
    "father_phone_number",
    "mother_name",
    "mother_phone_number",
    "category",
    "stream",
    "physically_handicapped",
    "family_income",
    "father_profession",
    "father_education_level",
    "mother_profession",
    "mother_education_level",
    "time_of_device_availability",
    "has_internet_access",
    "contact_hours_per_week",
    "is_dropper",
    "group",
]

USER_QUERY_PARAMS = [
    "date_of_birth",
    "phone",
    "whatsapp_phone",
    "id",
    "state",
    "district",
    "gender",
]

ENROLLMENT_RECORD_PARAMS = ["grade", "board_medium", "school_code", "school_name"]


def is_response_valid(response, error_message):
    if response.status_code == 200:
        return True
    raise HTTPException(status_code=500, detail=error_message)


def is_response_empty(response_data, error_message):
    if len(response_data) != 0:
        return response_data
    raise HTTPException(status_code=404, detail=error_message)


def school_data(
    form_attributes,
    priority,
    enrollment_record_data,
    student_response,
    returned_form_schema,
    total_number_of_fields,
    number_of_fields_left,
):
    if form_attributes[str(priority)]["key"] == "school_name":
        if enrollment_record_data["school_id"] is None:
            if student_response["user"]["district"] is None:
                if student_response["user"]["state"] is None:
                    returned_form_schema[
                        total_number_of_fields - number_of_fields_left
                    ] = form_attributes["state"]
                    number_of_fields_left -= 1

                else:
                    returned_form_schema[
                        total_number_of_fields - number_of_fields_left
                    ] = form_attributes["district"]
                    number_of_fields_left -= 1
            else:
                returned_form_schema[
                    total_number_of_fields - number_of_fields_left
                ] = form_attributes["school_name"]
                number_of_fields_left -= 1

    return returned_form_schema


@router.get("/form-schema")
def get_form_schema(request: Request):
    query_params = {}
    for key in request.query_params.keys():
        if key not in ["form_id"]:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]
    response = requests.get(form_db_url, params={"id": query_params["form_id"]})
    if response.status_code == 200:
        if len(response.json()) != 0:
            return response.json()
        raise HTTPException(status_code=404, detail="Program does not exist!")
    raise HTTPException(status_code=404, detail="Program does not exist!")


@router.get("/student-form")
def get_student_fields(request: Request):
    query_params = {}

    # check for valid query parameters and build the query_param object
    for key in request.query_params.keys():
        if key not in ["number_of_fields", "group", "student_id"]:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    # get the field ordering for a particular group
    form_group_mapping_response = requests.get(
        form_db_url, params={"name": FORM_GROUP_MAPPING[query_params["group"]]}
    )

    if is_response_valid(
        form_group_mapping_response, "Could not fetch form-group mapping!"
    ):
        form = is_response_empty(
            form_group_mapping_response.json(), "Form-group mapping does not exist!"
        )

        # get student data for the student ID that is requesting for profile completion
        # ASSUMPTION : student_id is valid and exists because only valid students will reach profile completion
        student_response = student.get_students(
            build_request(query_params={"student_id": query_params["student_id"]})
        )[0]

        # get enrollment data for the student
        enrollment_record_response = requests.get(
            enrollment_record_db_url, params={"student_id": student_response["id"]}
        )
        if is_response_valid(
            enrollment_record_response,
            "Could not fetch enrollment data for the student!",
        ):

            # get the priorities for all fields and sort them
            priority_order = sorted([eval(i) for i in form[0]["attributes"].keys()])

            # get the form attributes
            form_attributes = form[0]["attributes"]
            # number of fields to sent back to the student
            total_number_of_fields = number_of_fields_left = int(
                query_params["number_of_fields"]
            )

            returned_form_schema = {}

            for priority in priority_order:

                if number_of_fields_left > 0:

                    # if the form field is first name of last name, we check if full name exists in the database
                    if (
                        form_attributes[str(priority)]["key"] == "first_name"
                        or form_attributes[str(priority)]["key"] == "last_name"
                    ):
                        if student_response["user"]["full_name"] is None:
                            returned_form_schema[
                                total_number_of_fields - number_of_fields_left
                            ] = form_attributes[str(priority)]
                            number_of_fields_left -= 1

                    # if the form field is a user table attribute, we check in the user table
                    elif form_attributes[str(priority)]["key"] in USER_QUERY_PARAMS:
                        if (
                            student_response["user"][
                                form_attributes[str(priority)]["key"]
                            ]
                            is None
                        ):
                            returned_form_schema[
                                total_number_of_fields - number_of_fields_left
                            ] = form_attributes[str(priority)]
                            number_of_fields_left -= 1

                    # if the form field is a enrollment record table attribute, we check in the enrollement record table
                    elif (
                        form_attributes[str(priority)]["key"]
                        in ENROLLMENT_RECORD_PARAMS
                    ):
                        enrollment_record_data = enrollment_record_response.json()[0]
                        # check if enrollment record exists for this student
                        if enrollment_record_data != []:
                            # if the form field is school name, we check if school id exists in the enrollment record
                            if form_attributes[str(priority)]["key"] == "school_name":
                                if enrollment_record_data["school_id"] is None:
                                    returned_form_schema = school_data(
                                        form_attributes,
                                        priority,
                                        enrollment_record_data[0],
                                        student_response,
                                        returned_form_schema,
                                        total_number_of_fields,
                                        number_of_fields_left,
                                    )

                            else:
                                if (
                                    enrollment_record_data[
                                        form_attributes[str(priority)]["key"]
                                    ]
                                    is None
                                ):
                                    returned_form_schema[
                                        total_number_of_fields - number_of_fields_left
                                    ] = form_attributes[str(priority)]
                                    number_of_fields_left -= 1

                        else:
                            if form_attributes[str(priority)]["key"] == "school_name":
                                returned_form_schema[
                                    total_number_of_fields - number_of_fields_left
                                ] = [
                                    x
                                    for x in list(form_attributes.values())
                                    if x["key"] == "state"
                                ][
                                    0
                                ]
                                number_of_fields_left -= 1

                    else:
                        if (
                            student_response[form_attributes[str(priority)]["key"]]
                            is None
                        ):
                            returned_form_schema[
                                total_number_of_fields - number_of_fields_left
                            ] = form_attributes[str(priority)]
                            number_of_fields_left -= 1

            return returned_form_schema
