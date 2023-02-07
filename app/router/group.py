from fastapi import APIRouter, HTTPException
import requests
from settings import settings
from models import GroupResponse

router = APIRouter(prefix="/group", tags=["Group"])
group_db_url = settings.db_url + "/group/"


@router.get("/{group_id}")
def get_group_data(group_id: str, response_model=GroupResponse):
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
    query_params = {"name": group_id, "type": "group"}
    response = requests.get(group_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) != 0:
            return response.json()
        return HTTPException(status_code=404, detail="Group does not exist!")
    return HTTPException(status_code=response.status_code, detail=response.errors)
