from fastapi import HTTPException
from settings import settings


def is_response_valid(response, error_message=""):
    if response.status_code == 200:
        return True
    elif response.status_code == 201:
        return True
    if error_message:
        raise HTTPException(status_code=500, detail=error_message)
    return False


def is_response_empty(response_data, return_boolean, error_message=""):
    if len(response_data) != 0:
        return response_data
    if return_boolean:
        if error_message:
            raise HTTPException(status_code=404, detail=error_message)
        else:
            return False
    return []


def validate_and_build_query_params(data, valid_query_params):
    query_params = {}
    for key in data.keys():
        if key not in valid_query_params:
            raise HTTPException(
                status_code=400, detail="Query Parameter {} is not allowed!".format(key)
            )
        query_params[key] = data[key]

    return query_params


def db_request_token():
    print(settings.token)
    return {"Authorization": f"Bearer {settings.token}"}
