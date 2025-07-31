import random
import datetime
from dateutil.relativedelta import relativedelta
from services.school_service import get_school_by_name_and_region


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
        school_data = get_school_by_name_and_region(name=self.school_name, region=self.region)
        return school_data.get("code") if school_data else None

    def generate_three_digit_code(code=""):
        for _ in range(3):
            code += random.randint(0, 9)
        return code
