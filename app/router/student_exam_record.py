from fastapi import APIRouter, Request
import requests
from router import routes
import helpers
from helpers import db_request_token

router = APIRouter(prefix="/student-exam-record", tags=["Student Exam Record"])


@router.get("/")
def get_student_exam_record(request: Request):
    query_params = helpers.validate_and_build_query_params(
        request.query_params, ["id", "student_id","exam_id", "applciation_number","application_password", "date", "score", "rank"]
    )
    response = requests.get(
        routes.student_exam_record_db_url, params=query_params, headers=db_request_token()
    )
    print(response)
    if helpers.is_response_valid(response, "Student Exam Record API could not fetch the data!"):
        return response.json()


@router.post("/")
async def create_student_exam_record(request: Request):
    data = await request.body()
    response = requests.post(routes.student_exam_record_db_url, data=data, headers=db_request_token())
    if helpers.is_response_valid(response, "Exam API could not post the data!"):
        return helpers.is_response_empty(
            response.json(), "Exam API could not fetch the created record!"
        )


@router.patch("/")
async def update_student_exam_record(request: Request):
    data = await request.body()
    response = requests.patch(
        routes.student_exam_record_db_url + "/" + str(data["id"]),
        data=data,
        headers=db_request_token(),
    )
    if helpers.is_response_valid(response, "Exam API could not patch the data!"):
        return helpers.is_response_empty(
            response.json(), "Exam API could not fetch the patched record!"
        )
