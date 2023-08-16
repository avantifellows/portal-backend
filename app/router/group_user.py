from fastapi import APIRouter, Request
import requests
from models import GroupResponse
from router import routes
import helpers
import mapping

router = APIRouter(prefix="/group-user", tags=["Group User"])


@router.get("/", response_model=GroupResponse)
def get_group_user(request: Request):
    query_params = helpers.validate_and_build_query_params(
        request.query_params, mapping.GROUP_QUERY_PARAMS
    )

    response = requests.get(routes.group_db_url, params=query_params)
    if helpers.is_response_valid(response, "Group API could not fetch the data!"):
        return helpers.is_response_empty(
            response.json()[0], False, "Group record does not exist!"
        )
