from fastapi import APIRouter
import requests
from models import UserSession
from datetime import datetime
from router import routes
import helpers

router = APIRouter(prefix="/user-session", tags=["User-Session"])

@router.post("/")
def user_session_data(user_session: UserSession):
    """
    This function creates a new user session and stores it in the database.

    Parameters:
    user_session (UserSession): The user session object containing the session data.

    Returns:
    dict: Returns the created user session record if the creation is successful. If the creation fails, an error message is returned.

    Example:
    POST $BASE_URL/user_session_data
    Request Body:
    {
        "user_id": 1234,
        "session_id": "abcd1234",
        "start_time": "2023-07-04T12:30:00"
    }
    Response:
    {
        "user_id": 1234,
        "session_id": "abcd1234",
        "start_time": "2023-07-04T12:30:00"
    }
    """
    query_params = user_session.dict()
    query_params["start_time"] = datetime.now().isoformat()
    response = requests.post(routes.user_session_db_url, json=query_params)
    if helpers.is_response_valid(response, "User-session API could not post the data!"):
        helpers.is_response_empty(response.json(), "User-session API could not fetch the created record!")
