from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from router import student
from request import build_request

router = APIRouter(prefix="/form-schema", tags=["Form"])
form_db_url = settings.db_url + "/form-schema"
student_db_url = settings.db_url + "/student"
enrollment_record_db_url = settings.db_url + "/enrollment-record"

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


@router.get("/")
def get_form_schema(request: Request):
    query_params = {}
    for key in request.query_params.keys():
        if key not in ["form_name"]:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]
    response = requests.get(form_db_url, params={"name": query_params["form_name"]})
    if response.status_code == 200:
        if len(response.json()) != 0:
            return response.json()
        raise HTTPException(status_code=404, detail="Program does not exist!")
    raise HTTPException(status_code=404, detail="Program does not exist!")


@router.get("/student-form")
def get_student_fields(request: Request):
    query_params = {}
    for key in request.query_params.keys():
        if key not in ["number_of_fields", "form_name", "student_id"]:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(form_db_url, params={"name": query_params["form_name"]})
    if response.status_code == 200:
        if len(response.json()) != 0:
            form = response.json()
            response = student.get_students(
                build_request(query_params={"student_id": query_params["student_id"]})
            )[0]
            enrollment_record_response = requests.get(
                enrollment_record_db_url,
                params={"student_id": query_params["student_id"]},
            )
            priority_order = sorted(form[0]["attributes"].keys())
            form_attributes = form[0]["attributes"]
            print(response)
            returned_form_schema = {}
            number_of_fields = int(query_params["number_of_fields"])
            for priority in priority_order:
                if number_of_fields > 0:
                    if (
                        form_attributes[priority]["key"] == "first_name"
                        or form_attributes[priority]["key"] == "last_name"
                    ):
                        if response["user"]["full_name"] is None:
                            returned_form_schema[
                                5 - number_of_fields
                            ] = form_attributes[priority]
                            number_of_fields -= 1
                    elif form_attributes[priority]["key"] in USER_QUERY_PARAMS:
                        if response["user"][form_attributes[priority]["key"]] is None:
                            returned_form_schema[
                                5 - number_of_fields
                            ] = form_attributes[priority]
                            number_of_fields -= 1
                    elif form_attributes[priority]["key"] in ENROLLMENT_RECORD_PARAMS:
                        if (
                            enrollment_record_response[form_attributes[priority]["key"]]
                            is None
                        ):
                            returned_form_schema[
                                5 - number_of_fields
                            ] = form_attributes[priority]
                            number_of_fields -= 1
                    else:
                        if response[form_attributes[priority]["key"]] is None:
                            returned_form_schema[
                                5 - number_of_fields
                            ] = form_attributes[priority]
                            number_of_fields -= 1
            return returned_form_schema

        raise HTTPException(status_code=404, detail="Program does not exist!")
    raise HTTPException(status_code=404, detail="Program does not exist!")
