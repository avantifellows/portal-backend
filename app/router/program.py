from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings

router = APIRouter(prefix="/program", tags=["Program"])
program_db_url = settings.db_url + "/program/"

QUERY_PARAMS = [
    "id",
    "name",
    "type",
    "sub_type",
    "mode",
    "start_date",
    "target_outreach",
    "product_used",
    "donor",
    "state",
    "model",
    "group_id",
]


@router.get("/")
def get_program_data(request: Request):
    """
    This API returns details of a program corresponding to the provided program ID, if the ID exists in the database.

    Parameters:
    id (int): The ID against which details need to be retrieved.

    Returns:
    list: Returns program details if the program ID exists in the database. If the ID does not exist, a 404 status code is returned with a message indicating that the program ID does not exist.

    Example:
    > $BASE_URL/program/1234
    Returns: [{program_data}]

    > $BASE_URL/program/{invalid_id}
    Returns: {
        "status_code": 404,
        "detail": "Program ID does not exist!",
        "headers": null
    }
    """
    query_params = {}
    for key in request.query_params.keys():
        if key not in QUERY_PARAMS:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(program_db_url, params=query_params)
    if response.status_code == 200:
        if len(response.json()) != 0:
            return response.json()
        raise HTTPException(status_code=404, detail="Program does not exist!")
    raise HTTPException(status_code=404, detail="Program does not exist!")
