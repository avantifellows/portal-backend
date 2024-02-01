from fastapi import HTTPException
import requests
from settings import settings
import random
from helpers import db_request_token, is_response_valid, is_response_empty
from request import build_request
from router import (
    user as user_router,
    student as student_router,
    school,
    enrollment_record,
)

school_db_url = settings.db_url + "/school"


async def JNV_ID_generation(parameters):
    record_already_exist, ID = dedupe_for_users(parameters)

    if record_already_exist:
        return [not record_already_exist, ID]
    else:
        counter = 1000
        while counter > 0:
            id = (
                get_class_code(parameters["grade"])
                + get_jnv_code(parameters["region"], parameters["school_name"])
                + generate_three_digit_code()
            )

            duplicate_id = await check_for_duplicate_ID(id)
            if not duplicate_id:
                return [True, id]

            else:
                counter -= 1
    raise HTTPException(
        status_code=500, detail="ID could not be generated, max loops hit!"
    )


def dedupe_for_users(parameters):
    # check if the keys used for deduping exist in the request data
    for key in ["grade", "date_of_birth", "school_name", "gender", "category"]:
        if key not in parameters or parameters[key] == "" or parameters[key] is None:
            raise HTTPException(
                status_code=400,
                detail="{} is not part of the request data".format(key),
            )

    does_user_already_exist = user_router.get_users(
        build_request(
            query_params={
                "date_of_birth": parameters["date_of_birth"],
                "gender": parameters["gender"],
            }
        )
    )

    if len(does_user_already_exist) == 0:
        # if user does not exist, go ahead with ID generation
        return [False, ""]

    else:
        number_of_students_matching_user = []
        # if user does exist, check corresponding student attributes
        for user in does_user_already_exist:
            matching_student = student_router.get_students(
                build_request(
                    query_params={
                        "user_id": user["id"],
                        "category": parameters["category"],
                    }
                )
            )
            if len(matching_student) > 0:
                number_of_students_matching_user.append(matching_student[0])
        print(len(number_of_students_matching_user))

        if len(number_of_students_matching_user) == 0:
            # if user is found, but a matching student is not found, then go ahead with ID generation
            return [False, ""]

        else:
            # first, get the school ID based on the school name given in the request
            school_id_response = school.get_school(
                build_request(
                    query_params={
                        "name": parameters["school_name"],
                        "state": parameters["state"],
                        "district": parameters["district"],
                    }
                )
            )

            if len(school_id_response) > 0:
                # check if any of the found students study in the school
                for student in number_of_students_matching_user:
                    does_enrollment_record_exist = (
                        enrollment_record.get_enrollment_record(
                            build_request(
                                query_params={
                                    "school_id": school_id_response[0]["id"],
                                    "student_id": student["id"],
                                    "grade": parameters["grade"],
                                }
                            )
                        )
                    )

                    if len(does_enrollment_record_exist) > 0:
                        return [True, student["student_id"]]
                return [False, ""]
            else:
                raise HTTPException(status_code=404, detail="School does not exist!")


def get_class_code(grade):
    class_codes = {"9": "26", "10": "25", "11": "24", "12": "23"}
    return class_codes[grade]


def get_jnv_code(region, school_name):
    response = requests.get(
        school_db_url,
        params={
            "region": region,
            "name": school_name,
        },
        headers=db_request_token(),
    )

    if response.status_code == 200:
        if len(response.json()) == 0:
            raise HTTPException(status_code=404, detail="JNV or region does not exist!")
        return response.json()[0]["code"]

    return HTTPException(status_code=response.status_code, detail=response.errors)


def generate_three_digit_code():
    code = ""
    for _ in range(3):
        code += str(random.randint(0, 9))
    return code


async def check_for_duplicate_ID(id):
    return await student_router.verify_student(build_request(), student_id=id)
