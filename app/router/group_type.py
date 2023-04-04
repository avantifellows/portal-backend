from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings

router = APIRouter(prefix="/group-type", tags=["GroupType"])
group_type_db_url = settings.db_url + "/group-type/"


@router.get("/")
def get_group_type_data(request: Request):
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
    query_params = {}
    for key in request.query_params.keys():
        if key not in ["id", "type", "child_id"]:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(group_type_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) != 0:
            return response.json()
        raise HTTPException(status_code=404, detail="GroupType does not exist!")
    raise HTTPException(status_code=404, detail="GroupType does not exist!")
