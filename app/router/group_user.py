from fastapi import APIRouter, Request
import requests
from models import GroupUserResponse
from router import routes
import helpers
import mapping

router = APIRouter(prefix="/group-user", tags=["Group User"])

GROUP_USER_QUERY_PARAMS = ["user_id", "group_type_id", "id"]


@router.get("/", response_model=GroupUserResponse)
def get_group_user(request: Request):
    query_params = helpers.validate_and_build_query_params(
        request.query_params, mapping.GROUP_USER_QUERY_PARAMS
    )

    response = requests.get(routes.group_user_db_url, params=query_params)
    if helpers.is_response_valid(response, "Group-User API could not fetch the data!"):
        return helpers.is_response_empty(
            response.json()[0], False, "Group-User record does not exist!"
        )


@router.post("/")
async def create_group_user(request: Request):
    data = await request.body()
    print(data)
    response = requests.post(routes.group_user_db_url, data=data)
    if helpers.is_response_valid(response, "Group-User API could not post the data!"):
        return helpers.is_response_empty(
            response.json(), "Group-User API could not fetch the created record!"
        )
