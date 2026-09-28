import json
from typing import Any, Dict

import boto3

from models import AttendanceMessageSchema
from settings import settings


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
                QueueUrl=self.queue_url,
                MessageBody=json.dumps([message.dict()]),
            )
            print(f"Message sent. MessageId: {response['MessageId']}")
            return {"success": True, "message_id": response["MessageId"]}
        except Exception as e:
            print(f"Error sending message: {str(e)}")


sqs_service = SQSService()
