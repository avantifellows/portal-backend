from fastapi import APIRouter, Request
import requests
from router import routes
import helpers
import mapping

router = APIRouter(prefix="/group-type", tags=["GroupType"])


@router.get("/")
def get_group_type(request: Request):
    """
    This API returns details of a group-type based on the provided ID, if it exists in the database. The group-type is identified by a combination of type and child_id, where the child_id corresponds to the ID of either the program, group, or batch table, depending on the type of the group.

    Parameters:
    id (int): The ID against which details need to be retrieved
    type (str): The type of the group-type being retrieved. Must be one of "group", "program", or "batch"
    child_id (int): The ID of the corresponding table depending on the type of group-type being retrieved.

    Returns:
    list: Returns group-type details if the ID exists in the database, 404 otherwise.

    Example:
    > $BASE_URL/group-type?type=program&child_id=5678
    returns [{group_type_data}]

    > $BASE_URL/group-type?type=program&child_id=invalid_id
    returns {
        "status_code": 404,
        "detail": "GroupType ID does not exist!",
        "headers": null
    }
    """
    query_params = helpers.validate_and_build_query_params(
        request, mapping.GROUP_TYPE_QUERY_PARAMS
    )
    response = requests.get(routes.group_type_db_url, params=query_params)
    if helpers.is_response_valid(response, "Group-type API could not fetch the data!"):
        return helpers.is_response_empty(
            response.json(), False, "Group-type record does not exist!"
        )


@router.post("/")
async def create_group_type(request: Request):
    """
    This API creates a new group type based on the provided data.

    Parameters:
    request (Request): The request object containing the data for creating the group type.

    Returns:
    dict: Returns the created group type record if the creation is successful. If the creation fails, an error message is returned.

    Example:

    POST $BASE_URL/create_group_type
    Request Body:
    {
        "id": "123",
        "type": "group",
        "child_id": 1
    }
    Response:
    {
        "id": "123",
        "type": "group",
        "child_id": 1
    }
    """
    data = await request.body()
    response = requests.post(routes.group_type_db_url, data=data)
    if helpers.is_response_valid(response, "Group-type API could not post the data!"):
        return helpers.is_response_empty(
            response.json(), "Group-type API could not fetch the created record!"
        )


@router.patch("/")
async def update_group_type(request: Request):
    """
    This API updates an existing group type based on the provided data.

    Parameters:
    request (Request): The request object containing the data for updating the group type.

    Returns:
    dict: Returns the updated group type record if the update is successful. If the update fails, an error message is returned.

    Example:
    PATCH $BASE_URL/update_group_type
    Request Body:
    {
        "id": 123,
        "type": "program",
    }
    Response:
    {
        "id": 123,
        "type": "program",
        "child_id": 1
    }
    """
    data = await request.body()
    response = requests.patch(
        routes.group_type_db_url + "/" + str(data["id"]), data=data
    )
    if helpers.is_response_valid(response, "Group-type API could not patch the data!"):
        return helpers.is_response_empty(
            response.json(), "Group-type API could not fetch the patched record!"
        )
