from fastapi import APIRouter
import requests
from settings import settings
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/group", tags=["Group"])

@router.post("/get-group-data")
def get_session_data(group_id: str):
    r = requests.get(settings.db_url + "group/" + group_id)
    group_data = r.json()
    if "errors" not in group_data:
            return group_data
    return JSONResponse("Group not found")