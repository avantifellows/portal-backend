from fastapi import HTTPException
import requests
from settings import settings
import random

school_db_url = settings.db_url + "/school"


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

    def get_id(self):
        return self.id

    def get_class_code(self):
        class_codes = {"9": "26", "10": "25", "11": "24", "12": "23"}
        return class_codes[self.grade]

    def get_jnv_code(self):
        response = requests.get(
            school_db_url, params={"region": self.region, "name": self.school_name}
        )
        if response.status_code == 200:
            if len(response.json()) == 0:
                return HTTPException(
                    status_code=404, detail="JNV or region does not exist!"
                )
            return response.json()
        return HTTPException(status_code=response.status_code, detail=response.errors)

    def generate_three_digit_code(code=""):
        for _ in range(3):
            code += random.randint(0, 9)
        return code
