from fastapi import HTTPException
import requests
from settings import settings
import random
from helpers import db_request_token, is_response_valid, is_response_empty
from request import build_request
from router import user as user_router, student as student_router, school, enrollment_record

school_db_url = settings.db_url + "/school"


class JNVIDGeneration:
    def __init__(self, parameters):
        self.parameters = parameters

        record_already_exist, ID = self.dedupe_for_users()
        if record_already_exist:
            self.id = ID

        else:
            counter = 1000
            while counter > 0:
                id = (
                    self.get_class_code()
                    + self.get_jnv_code()
                    + self.generate_three_digit_code()
                )

                if not self.check_for_duplicate_ID(id):
                    self.id = id
                    break
                counter -= 1

    def dedupe_for_users(self):

        # check if the keys used for deduping exist in the request data
        for key in ["grade", "date_of_birth", "school_name", "gender", "category"]:
            if key not in self.parameters or self.parameters[key] == "" or self.parameters[key] is None:
                raise HTTPException(
                status_code=400, detail="{} is not part of the request data".format(key)
                )

        does_user_already_exist = user_router.get_users(
            build_request(
                query_params={ 'date_of_birth': self.parameters['date_of_birth'], 'gender':self.parameters['gender']}
            ))
        if len(does_user_already_exist) == 0:
            # if user does not exist, go ahead with ID generation
            return [False, '']

        else:
            # if user does exist, check corresponding student attributes
            for user in does_user_already_exist:
                does_student_already_exist = student_router.get_students(
            build_request(
                query_params={ 'user_id': user['id'], 'category':self.parameters['category'], 'grade': self.parameters['grade']}
            ))

                if len(does_student_already_exist) == 0:
                    # if user is found, but a matching student is not found, then go ahead with ID generation
                    return [False, '']

                else:
                    # first, get the school ID based on the school name given in the request
                    school_id_response = school.get_school(build_request(query_params={'name': self.parameters['school_name']}))
                    if is_response_valid(school_id_response, "School ID could not be retrieved"):
                        school_id = is_response_empty(school_id_response.json())[0]

                        # check if any of the found students study in the school
                        for student in does_student_already_exist:
                            does_enrollment_record_exist = enrollment_record.get_enrollment_record(build_request(query_params={'school_id': school_id, 'student_id': student['id']}))
                            if len(does_enrollment_record_exist) == 0:
                                return [False, '']
                            else:
                                return [True, student['student_id']]


    def get_id(self):
        return self.id

    def get_class_code(self):
        class_codes = {"9": "26", "10": "25", "11": "24", "12": "23"}
        return class_codes[self.parameters['grade']]

    def get_jnv_code(self):
        response = requests.get(
            school_db_url, params={"region": self.parameters['region'], "name": self.parameters['school_name']}, headers=db_request_token()
        )
        if response.status_code == 200:
            if len(response.json()) == 0:
                return HTTPException(
                    status_code=404, detail="JNV or region does not exist!"
                )
            return response.json()[0]["code"]

        return HTTPException(status_code=response.status_code, detail=response.errors)

    def generate_three_digit_code(self):
        code = ""
        for _ in range(3):
            code += str(random.randint(0, 9))
        return code


    async def check_for_duplicate_ID(self, id):
        return await student.verify_student(build_request(), student_id=id)
