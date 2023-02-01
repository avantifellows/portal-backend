from fastapi import APIRouter, HTTPException
import requests
from settings import settings

router = APIRouter(prefix="/group", tags=["Group"])
group_db_url = settings.db_url + "group/"


@router.get("/get-group-data/{group_id}")
def get_group_data(group_id: str):
    """
    API to get details about a group
    """
    query_params = {"group_id": group_id}
    response = requests.get(group_db_url, params=query_params)
    if response.status_code == 200:
        return response.json()
    return HTTPException(status_code=response.status_code, detail=response.errors)
