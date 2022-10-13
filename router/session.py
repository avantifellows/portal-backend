from fastapi import APIRouter
from database import create_db_connection

router = APIRouter(prefix="/session", tags=["Session"])


@router.get("/get_session_data")
def get_session_data(session_id: str):
    cursor = create_db_connection()
    print(cursor)
