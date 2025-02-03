from fastapi import APIRouter, HTTPException
import requests
from models import UserSession, AttendanceMessageSchema
from datetime import datetime
from routes import user_session_db_url
from helpers import db_request_token, is_response_valid, is_response_empty
from router import student, session, teacher, school
from request import build_request
from settings import settings
import boto3
from typing import Dict, Any
import json


class SQSService:
    def __init__(self):
        self.sqs_client = boto3.client(
            "sqs",
            region_name="ap-south-1",
            aws_access_key_id=settings.SQS_ACCESS_KEY,
            aws_secret_access_key=settings.SQS_SECRET_ACCESS_KEY,
        )
        self.queue_url = settings.AWS_SQS_URL

    async def send_message(self, message: AttendanceMessageSchema) -> Dict[str, Any]:
        try:
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url, MessageBody=json.dumps([message.dict()])
            )
            print(f"Message sent. MessageId: {response['MessageId']}")
            return {"success": True, "message_id": response["MessageId"]}
        except Exception as e:
            print(f"Error sending message: {str(e)}")


router = APIRouter(prefix="/user-session", tags=["User-Session"])
sqs_service = SQSService()


@router.post("/send-message")
async def send_message(message: AttendanceMessageSchema):
    try:
        response = await sqs_service.send_message(message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def user_session(user_session: UserSession):
    query_params = user_session.dict()
    query_params["timestamp"] = datetime.now().isoformat()

    if query_params["user_type"] == "student":
        user_id_response = student.get_students(
            build_request(query_params={"student_id": query_params["user_id"]})
        )
        query_params["user_id"] = user_id_response[0]["user"]["id"]
    elif query_params["user_type"] == "teacher":
        user_id_response = teacher.get_teachers(
            build_request(query_params={"teacher_id": query_params["user_id"]})
        )
        query_params["user_id"] = user_id_response[0]["user"]["id"]
    elif query_params["user_type"] == "school":
        user_id_response = school.get_school(
            build_request(query_params={"code": query_params["user_id"]})
        )
        query_params["user_id"] = user_id_response["user"]["id"]

    session_pk_id_response = await session.get_session(
        build_request(query_params={"session_id": query_params["session_id"]})
    )
    query_params["session_id"] = session_pk_id_response[0]["id"]

    response = requests.post(
        user_session_db_url, json=query_params, headers=db_request_token()
    )

    if is_response_valid(response, "User-session API could not post the data!"):
        is_response_empty(
            response.json(), "User-session API could not fetch the created record!"
        )
