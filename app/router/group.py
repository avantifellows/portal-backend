from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from models import GroupResponse

router = APIRouter(prefix="/group", tags=["Group"])
group_db_url = settings.db_url + "/group/"


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
    query_params = {}
    for key in request.query_params.keys():
        if key not in ["name", "id", "input_schema", "locale", "locale_data"]:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(group_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) != 0:
            return response.json()[0]
        raise HTTPException(status_code=404, detail="Group does not exist!")
    raise HTTPException(status_code=404, detail="Group does not exist!")
