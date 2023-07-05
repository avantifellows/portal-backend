from fastapi import APIRouter, Request
import requests
from router import routes
import helpers

router = APIRouter(prefix="/batch", tags=["Batch"])

@router.get("/")
def get_batch(request: Request):
    """
    This API retrieves batch data based on the provided query parameters.

    Parameters:
    request (Request): The request object containing the query parameters.

    Returns:
    list: Returns the batch data that matches the provided query parameters. If no batch matches the parameters, an error message is returned.

    Example:

        GET $BASE_URL/get_batch?id=1234&name=math&contact_hours_per_week=3
        Response:
        {
        "status_code": 200,
        "detail": "Batch data retrieved successfully!",
        "batch_data": [{matching_batch_data}],
        "headers": null
        }

        GET $BASE_URL/get_batch?id=5678
        Response:
        {
        "status_code": 404,
        "detail": "Batch does not exist!",
        "headers": null
        }
    """
    query_params = helpers.validate_and_build_query_params(
        request.query_params, ["id", "name", "contact_hours_per_week"]
    )
    response = requests.get(routes.batch_db_url, params=query_params)
    if helpers.is_response_valid(response, "Batch API could not fetch the data!"):
        return helpers.is_response_empty(
            response.json(), False, "Batch does not exist!"
        )


@router.post("/")
async def create_batch(request:Request):
    """
    This API creates a new batch in the database.

    Parameters:
    request (Request): The request object containing the batch data to be created.

    Returns:
    list: Returns the created batch record if the creation is successful. If the creation fails, an error message is returned.

    Example:

        POST $BASE_URL/create_batch
        Request body: {batch_data}
        Response:
        {
        "status_code": 200,
        "detail": "Batch created successfully!",
        "batch_record": {created_batch_data},
        "headers": null
        }

        POST $BASE_URL/create_batch
        Request body: {invalid_batch_data}
        Response:
        {
        "status_code": 500,
        "detail": "Batch API could not post the data!",
        "headers": null
        }
    """

    data = await request.body()
    response = requests.post(routes.batch_db_url, data=data)
    if helpers.is_response_valid(response, "Batch API could not post the data!"):
        return helpers.is_response_empty(
            response.json(), "Batch API could not fetch the created record!"
        )


@router.patch("/")
async def update_batch(request:Request):
    """
    This API updates an existing batch record in the database.

    Parameters:
    request (Request): The request object containing the updated batch data.

    Returns:
    list: Returns the updated batch record if the update is successful. If the update fails, an error message is returned.

    Example:

        PATCH $BASE_URL/update_batch
        Request body: {updated_batch_data}
        Response:
        {
        "status_code": 200,
        "detail": "Batch updated successfully!",
        "batch_record": {updated_batch_data},
        "headers": null
        }

        PATCH $BASE_URL/update_batch
        Request body: {invalid_batch_data}
        Response:
        {
        "status_code": 500,
        "detail": "Batch API could not patch the data!",
        "headers": null
        }
    """
    data = await request.body()
    response = requests.patch(
        routes.batch_db_url + "/" + str(data["id"]), data=data
    )
    if helpers.is_response_valid(response, "Batch API could not patch the data!"):
        return helpers.is_response_empty(
            response.json(), "Batch API could not fetch the patched record!"
        )