import requests
from settings import settings
from fastapi import HTTPException
from dateutil.relativedelta import relativedelta
from request import build_request
from logger_config import get_logger
from routes import student_db_url
from helpers import db_request_token

logger = get_logger()

COUNTER_FOR_JNV_ID_GENERATION = 1000


class EnableStudents:
    def __init__(self, data):
        for param in [
            "grade",
            "date_of_birth",
            "gender",
            "school_name",
            "category",
            "first_name",
            "region",
        ]:
            if param not in data:
                logger.error(f"{param} is required")
                raise ValueError(f"{param} is required")

        self.data = data
        self.student_id = self.generate_student_id()

    def generate_student_id(self):
        max_retries = 3
        for attempt in range(max_retries):
            payload = {
                "grade": self.data["grade"],
                "date_of_birth": self.data["date_of_birth"],
                "gender": self.data["gender"],
                "school_name": self.data["school_name"],
                "region": self.data["region"],
                "category": self.data["category"],
                "first_name": self.data["first_name"],
            }
            response = requests.post(
                student_db_url + "/generate-id",
                json=payload,
                headers=db_request_token(),
            )
            if response.status_code in [200, 201]:
                return response.json()["student_id"]
            else:
                error_message = response.json().get("error", "Unknown error occurred")
                logger.error(f"Error generating student ID: {error_message}")
                if "Max attempts hit" in error_message:
                    if attempt < max_retries - 1:
                        logger.error(
                            f"Retrying... Attempt {attempt + 2} of {max_retries}"
                        )
                    else:
                        logger.error(
                            "Max retries reached. Unable to generate student ID."
                        )
                        break
                else:
                    break
        return ""

    def get_student_id(self):
        return self.student_id
