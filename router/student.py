from fastapi import APIRouter, HTTPException
import requests
from settings import settings

router = APIRouter(prefix="/student", tags=["Student"])
student_db_url = settings.db_url + "student/"

@router.post("/student-id-exists")
def student_id_exists(student_id: str):
    """
    API to check if a student ID exists
    """
    response = requests.get(student_db_url + student_id)
    if response.status_code == 200:
            return response.json()
    return HTTPException(status_code=response.status_code, detail=response.errors)