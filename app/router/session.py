from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from models import SessionOpenResponse

router = APIRouter(prefix="/session", tags=["Session"])
session_db_url = settings.db_url + "/session/"

@router.get("/", response_model=SessionOpenResponse)
async def get_session_data(request: Request):
    """
    This API returns session details corresponding to the provided session ID, if the ID exists in the database

    Parameters:
    session_id (str): The ID against which details need to be retrieved

    Returns:
    list: Returns session details if the session ID exists in the database. If the ID does not exist, 404 is returned

    Example:
    > $BASE_URL/session/1234
    returns [{session_data}]

    > $BASE_URL/session/{invalid_id}
    returns {
        "status_code": 404,
        "detail": "Session ID does not exist!",
        "headers": null
    }
    """
    query_params = {}
    for key in request.query_params.keys():
        if key not in ["name", "session_id"]:
            return HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(session_db_url, params=query_params)

    if response.status_code == 200:
        if len(response.json()) != 0:
            return response.json()[0]
        return HTTPException(status_code=404, detail="Session ID does not exist!")
    raise HTTPException(status_code=response.status_code, detail=response.errors)