from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings

router = APIRouter(prefix="/batch", tags=["Batch"])
batch_db_url = settings.db_url + "/batch/"


@router.get("/")
async def get_batch_data(request: Request):
    """
    This API returns batch details corresponding to the provided batch ID, if the ID exists in the database

    Parameters:
    batch_id (str): The ID against which details need to be retrieved

    Returns:
    list: Returns batch details if the batch ID exists in the database. If the ID does not exist, 404 is returned

    Example:
    > $BASE_URL/batch/1234
    returns [{batch_data}]

    > $BASE_URL/batch/{invalid_id}
    returns {
        "status_code": 404,
        "detail": "Batch ID does not exist!",
        "headers": null
    }
    """
    query_params = {}
    for key in request.query_params.keys():
        if key not in ["id", "name", "contact_hours_per_week"]:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = request.query_params[key]

    response = requests.get(batch_db_url, params=query_params)

    if response.status_code == 200:
        if len(response.json()) != 0:
            return response.json()[0]
        raise HTTPException(status_code=404, detail="Batch ID does not exist!")
    raise HTTPException(status_code=404, detail="Batch ID does not exist!")
