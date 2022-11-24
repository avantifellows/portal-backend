from fastapi import APIRouter
import requests
from settings import settings
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/group", tags=["Group"])
group_db_url = settings.db_url + "group/"

@router.post("/get-group-data")
def get_group_data(group_id: str):
    """
    API to get details about a group
    """
    group_data = requests.get(group_db_url + group_id).json()
    if "errors" not in group_data:
            return group_data
    return JSONResponse("Group not found")