from fastapi import APIRouter, Request
import requests
from router import routes
import helpers
import mapping

router = APIRouter(prefix="/school", tags=["School"])


@router.get("/")
def get_school(request: Request):
    query_params = helpers.validate_and_build_query_params(
        request.query_params, mapping.SCHOOL_QUERY_PARAMS
    )
    response = requests.get(routes.school_db_url, params=query_params)

    if helpers.is_response_valid(response, "School API could not fetch the data!"):

        return helpers.is_response_empty(
            response.json(), False, "School does not exist"
        )
