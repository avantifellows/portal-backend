from fastapi import APIRouter, Request
import requests
from models import GroupResponse
from router import routes
import helpers
import mapping

router = APIRouter(prefix="/group", tags=["Group"])


@router.get("/", response_model=GroupResponse)
def get_group_data(request: Request):
    """
    This API returns group details corresponding to the provided group ID, if the ID exists in the database

    Parameters:
    group_id (str): The ID against which details need to be retrieved

    Returns:
    list: Returns group details if the group ID exists in the database, 404 otherwise

    Example:
    > $BASE_URL/group/1234
    returns [{group_data}]

    > $BASE_URL/group/{invalid_id}
    returns {
        "status_code": 404,
        "detail": "Group ID does not exist!",
        "headers": null
    }
    """
    query_params = helpers.validate_and_build_query_params(
        request, mapping.GROUP_QUERY_PARAMS
    )
    response = requests.get(routes.group_type_db_url, params=query_params)
    if helpers.is_response_valid(response, "Group API could not fetch the data!"):
        return helpers.is_response_empty(
            response.json(), False, "Group record does not exist!"
        )


@router.post("/")
async def create_group(request: Request):
    """
    This API creates a new group based on the provided data.

    Parameters:
    request (Request): The request object containing the data for creating the group.

    Returns:
    dict: Returns the created group record if the creation is successful. If the creation fails, an error message is returned.

    Example:

    POST $BASE_URL/create_group
    Request Body:
    {
        "name": "ABC",
        "locale": "en"
    }
    Response:
    {
        "id": 12,
        "name": "ABC",
        "locale": "en"
    }
    """
    data = await request.body()
    response = requests.post(routes.group_db_url, data=data)
    if helpers.is_response_valid(response, "Group API could not post the data!"):
        return helpers.is_response_empty(
            response.json(), "Group API could not fetch the created record!"
        )


@router.patch("/")
async def update_group(request: Request):
    """
    This API updates an existing group based on the provided data.

    Parameters:
    request (Request): The request object containing the data for updating the group.

    Returns:
    dict: Returns the updated group record if the update is successful. If the update fails, an error message is returned.

    Example:
    PATCH $BASE_URL/update_group
    Request Body:
    {
        "id": 12,
        "locale": "hi",
    }
    Response:
    {
        "id": 12,
        "name": "ABC",
        "locale": "hi"
    }
    """
    data = await request.body()
    response = requests.patch(routes.group_db_url + "/" + str(data["id"]), data=data)
    if helpers.is_response_valid(response, "Group API could not patch the data!"):
        return helpers.is_response_empty(
            response.json(), "Group API could not fetch the patched record!"
        )
