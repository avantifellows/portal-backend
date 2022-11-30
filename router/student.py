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
    query_params = {'student_id':student_id}
    response = requests.get(student_db_url, params=query_params)
    if response.status_code == 200:
            return response.json()
    return HTTPException(status_code=response.status_code, detail=response.errors)

@router.post("/birthdate-matches")
def birthdate_matches(student_id:str, birth_date:str):
    """
    API to check if the given birthdate matches to the student ID
    """
    query_params = {'student_id':student_id, 'date_of_birth': birth_date}
    response = requests.get(student_db_url, params=query_params)
    if response.status_code == 200:
            return response.json()
    return HTTPException(status_code=response.status_code, detail=response.errors)