from settings import settings
import random
from router import school
import datetime
from dateutil.relativedelta import relativedelta
from request import build_request


class JNVIDGeneration:
    def __init__(self, region, school, grade):
        self.region = region
        self.school = school
        self.grade = grade
        self.id = (
            self.get_class_code()
            + self.get_jnv_code()
            + self.generate_three_digit_code()
        )

    def get_class_code(self):
        graduating_year = datetime.date.today() + relativedelta(
            years=12 - int(self.grade)
        )
        return str(graduating_year.year)[-2:]

    def get_jnv_code(self):
        return school.get_school(
            build_request(
                query_params={"region": self.region, "name": self.school_name}
            )
        )

    def generate_three_digit_code(code=""):
        for _ in range(3):
            code += random.randint(0, 9)
        return code
