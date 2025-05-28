from fastapi import APIRouter, HTTPException
import requests
from models import UserSession, AttendanceMessageSchema
from datetime import datetime
from routes import user_session_db_url
from helpers import (
    db_request_token,
    is_response_valid,
    is_response_empty,
    safe_get_first_item,
)
from router import student, session, teacher, school
from request import build_request
from settings import settings
import boto3
from typing import Dict, Any
import json
from logger_config import get_logger

logger = get_logger()


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
    try:
        query_params = user_session.dict()
        query_params["timestamp"] = datetime.now().isoformat()

        logger.info(
            f"Creating user session for user_type: {query_params.get('user_type')}, user_id: {query_params.get('user_id')}"
        )

        # Simple ID resolution without extensive validation
        if query_params["user_type"] == "student":
            try:
                user_id_response = student.get_students(
                    build_request(query_params={"student_id": query_params["user_id"]})
                )

                student_data = safe_get_first_item(
                    user_id_response, "Student not found"
                )
                if not isinstance(student_data, dict) or not student_data.get(
                    "user", {}
                ).get("id"):
                    raise HTTPException(status_code=404, detail="Student not found")

                query_params["user_id"] = student_data["user"]["id"]

            except Exception as e:
                logger.error(
                    f"Failed to resolve student_id {query_params['user_id']}: {str(e)}"
                )
                raise HTTPException(status_code=404, detail="Student not found")

        elif query_params["user_type"] == "teacher":
            try:
                user_id_response = teacher.get_teachers(
                    build_request(query_params={"teacher_id": query_params["user_id"]})
                )

                teacher_data = safe_get_first_item(
                    user_id_response, "Teacher not found"
                )
                if not isinstance(teacher_data, dict) or not teacher_data.get(
                    "user", {}
                ).get("id"):
                    raise HTTPException(status_code=404, detail="Teacher not found")

                query_params["user_id"] = teacher_data["user"]["id"]

            except Exception as e:
                logger.error(
                    f"Failed to resolve teacher_id {query_params['user_id']}: {str(e)}"
                )
                raise HTTPException(status_code=404, detail="Teacher not found")

        elif query_params["user_type"] == "school":
            try:
                user_id_response = school.get_school(
                    build_request(query_params={"code": query_params["user_id"]})
                )

                if not isinstance(user_id_response, dict) or not user_id_response.get(
                    "user", {}
                ).get("id"):
                    raise HTTPException(status_code=404, detail="School not found")

                query_params["user_id"] = user_id_response["user"]["id"]

            except Exception as e:
                logger.error(
                    f"Failed to resolve school code {query_params['user_id']}: {str(e)}"
                )
                raise HTTPException(status_code=404, detail="School not found")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported user_type: {query_params['user_type']}",
            )

        # Simple session validation
        try:
            session_pk_id_response = await session.get_session(
                build_request(query_params={"session_id": query_params["session_id"]})
            )

            session_data = safe_get_first_item(
                session_pk_id_response, "Session not found"
            )
            if not isinstance(session_data, dict) or "id" not in session_data:
                raise HTTPException(status_code=404, detail="Session not found")

            query_params["session_id"] = session_data["id"]

        except Exception as e:
            logger.error(
                f"Failed to resolve session_id {query_params['session_id']}: {str(e)}"
            )
            raise HTTPException(status_code=404, detail="Session not found")

        # Create user session record
        response = requests.post(
            user_session_db_url, json=query_params, headers=db_request_token()
        )

        if is_response_valid(response, "User-session API could not post the data!"):
            created_data = is_response_empty(
                response.json(),
                True,
                "User-session API could not fetch the created record!",
            )
            logger.info(
                f"Successfully created user session for user_type: {user_session.user_type}"
            )
            return created_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in user_session: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Unexpected error creating user session"
        )
