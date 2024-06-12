from settings import settings
from fastapi import HTTPException
import random
from router import school, student, user, enrollment_record
import datetime
from dateutil.relativedelta import relativedelta
from request import build_request
from logger_config import get_logger

logger = get_logger()


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

        self.grade = data["grade"]
        self.date_of_birth = data["date_of_birth"]
        self.gender = data["gender"]
        self.school_name = data["school_name"]
        self.category = data["category"]
        self.first_name = data["first_name"]
        self.region = data["region"]
        self.student_id = ""

        self.student_id = self.check_if_user_exists()

        if self.student_id != "":
            return self.student_id

        counter = settings.JNV_COUNTER_FOR_ID_GENERATION

        while counter > 0:
            id = (
                self.get_class_code()
                + self.get_jnv_code()
                + self.generate_three_digit_code()
            )

            if self.check_if_generated_id_already_exists(id):
                counter -= 1
            else:
                self.student_id = id
                break

        raise HTTPException(
            status_code=400,
            detail="JNV Student ID could not be generated. Max loops hit!",
        )

    def check_if_user_exists(
        self,
    ):
        # First, we check if a user with the same DOB, gender and first_name already exists in the database
        user_already_exists = user.get_users(
            build_request(
                query_params={
                    "date_of_birth": self.date_of_birth,
                    "gender": self.gender,
                    "first_name": self.first_name,
                }
            )
        )

        if len(user_already_exists) > 0:
            # If the user already exists, we check if a student with the same grade, category already exists
            student_already_exists = student.get_students(
                build_request(
                    query_params={
                        "grade": self.grade,
                        "category": self.category,
                    }
                )
            )
            if len(student_already_exists) > 0:
                # If the student already exists, we check if the student is already enrolled in the given school
                school_response = school.get_school(
                    build_request(query_params={"name": self.school_name})
                )

                if len(school_response) > 0:
                    # At this point, if there is a duplicate student, there should be only one, hence we return the student_id
                    enrollment_record_already_exists = (
                        enrollment_record.get_enrollment_records(
                            build_request(
                                query_params={
                                    "group_id": school_response[0].id,
                                    "group_type": "school",
                                    "user_id": student_already_exists[0]["user"]["id"],
                                }
                            )
                        )
                    )

                    if len(enrollment_record_already_exists) > 0:
                        logger.error("Student already exists in the database")
                        return student["student_id"]

        return ""

    def get_class_code(self):
        graduating_year = datetime.date.today() + relativedelta(
            years=12 - int(self.grade)
        )
        return str(graduating_year.year)[-2:]

    def get_jnv_code(self):
        school_response = school.get_school(
            build_request(
                query_params={"region": self.region, "name": self.school_name}
            )
        )
        return school_response["code"]

    def generate_three_digit_code(self, code=""):
        for _ in range(3):
            code += str(random.randint(0, 9))
        return code

    def get_student_id(self):
        return self.student_id

    def check_if_generated_id_already_exists(self, id):
        student_response = student.get_students(
            build_request(query_params={"student_id": id})
        )

        return len(student_response) != 0
