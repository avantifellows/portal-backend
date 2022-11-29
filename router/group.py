from fastapi import APIRouter, HTTPException
import requests
from settings import settings

router = APIRouter(prefix="/group", tags=["Group"])
group_db_url = settings.db_url + "group/"

@router.post("/get-group-data")
def get_group_data(group_id: str):
    """
    API to get details about a group
    """
    group_data = requests.get(group_db_url + group_id)
    if group_data.status_code == 200:
            return group_data.json()
    return HTTPException(status_code=group_data.status_code, detail=group_data.errors)
