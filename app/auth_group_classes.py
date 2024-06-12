from settings import settings
from fastapi import HTTPException
import random
from router import school, student, user, enrollment_record, grade
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

        self.student_id = self.check_if_student_exists()

        if self.student_id == "":
            counter = int(settings.JNV_COUNTER_FOR_ID_GENERATION)

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

            if counter == 0:
                raise HTTPException(
                    status_code=400,
                    detail="JNV Student ID could not be generated. Max loops hit!",
                )

    def check_if_enrolled_in_school(self, school_id, user_id):
        enrollment_record_already_exists = enrollment_record.get_enrollment_record(
            build_request(
                query_params={
                    "group_id": school_id,
                    "group_type": "school",
                    "user_id": user_id,
                }
            )
        )
        return enrollment_record_already_exists

    def check_if_user_exists(self, user_id):
        user_already_exists = user.get_users(
            build_request(
                query_params={
                    "id": user_id,
                    "date_of_birth": self.date_of_birth,
                    "gender": self.gender,
                    "first_name": self.first_name,
                }
            )
        )

        return user_already_exists

    def check_if_student_exists(self):
        grade_response = grade.get_grade(
            build_request(query_params={"number": self.grade})
        )
        # First, we check if a student with the same grade and category already exists in the database
        student_already_exists = student.get_students(
            build_request(
                query_params={
                    "grade_id": grade_response["id"],
                    "category": self.category,
                }
            )
        )

        if len(student_already_exists) > 0:
            for existing_student in student_already_exists:
                # If the student already exists, we check if a user with the same DOB, gender and first_name already exists
                user_already_exists = self.check_if_user_exists(
                    existing_student["user"]["id"]
                )

                if len(user_already_exists) > 0:
                    # If the student already exists, we check if the student is already enrolled in the given school
                    school_response = school.get_school(
                        build_request(query_params={"name": self.school_name})
                    )
                    for existing_user in user_already_exists:
                        enrollment_record_already_exists = (
                            self.check_if_enrolled_in_school(
                                school_response["id"], existing_user["id"]
                            )
                        )
                        # At this point, if there is a duplicate student, there should be only one, hence we return the student_id
                        if len(enrollment_record_already_exists) > 0:
                            logger.error("Student already exists in the database")
                            return existing_student["student_id"]

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
