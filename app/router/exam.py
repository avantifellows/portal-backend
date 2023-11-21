from fastapi import APIRouter, Request
import requests
from router import routes
import helpers
from helpers import db_request_token

router = APIRouter(prefix="/exam", tags=["Exam"])


@router.get("/")
def get_exam(request: Request):
    query_params = helpers.validate_and_build_query_params(
        request.query_params, ["id", "name", "registration_deadline", "date"]
    )

    response = requests.get(
        routes.exam_db_url, params=query_params, headers=db_request_token()
    )
    if helpers.is_response_valid(response, "Exam API could not fetch the data!"):
        return helpers.is_response_empty(
            response.json(), False, "Exam does not exist!"
        )


@router.post("/")
async def create_exam(request: Request):
    data = await request.body()
    response = requests.post(routes.exam_db_url, data=data, headers=db_request_token())
    if helpers.is_response_valid(response, "Exam API could not post the data!"):
        return helpers.is_response_empty(
            response.json(), "Exam API could not fetch the created record!"
        )


@router.patch("/")
async def update_exam(request: Request):
    data = await request.body()
    response = requests.patch(
        routes.exam_db_url + "/" + str(data["id"]),
        data=data,
        headers=db_request_token(),
    )
    if helpers.is_response_valid(response, "Exam API could not patch the data!"):
        return helpers.is_response_empty(
            response.json(), "Exam API could not fetch the patched record!"
        )
