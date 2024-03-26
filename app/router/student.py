from fastapi import APIRouter, HTTPException, Request
import requests
from settings import settings
from router import group, auth_group, group_user, user, school, grade
from id_generation_classes import JNVIDGeneration
from request import build_request
from routes import student_db_url
from helpers import (
    db_request_token,
    validate_and_build_query_params,
    is_response_valid,
    is_response_empty,
)
import json
from mapping import (
    USER_QUERY_PARAMS,
    STUDENT_QUERY_PARAMS,
    ENROLLMENT_RECORD_PARAMS,
    SCHOOL_QUERY_PARAMS,
)

router = APIRouter(prefix="/student", tags=["Student"])


def generate_JNV_student_id(data):
    counter = settings.JNV_COUNTER_FOR_ID_GENERATION

    if counter > 0:
        JNV_Id = JNVIDGeneration(
            data["region"], data["school_name"], data["grade"]
        ).get_id
        counter -= 1
        return JNV_Id

    raise HTTPException(
        status_code=400, detail="JNV Student ID could not be generated. Max loops hit!"
    )


async def create_school_user_record(data, school_name):
    school_data = school.get_school(build_request(query_params={"name": school_name}))
    group_data = group.get_group(
        build_request(
            query_params={"child_id": school_data["id"], "type": "auth_group"}
        )
    )

    await group_user.create_group_user(
        build_request(
            method="POST",
            body={"group_id": group_data["id"], "user_id": data["user"]["id"]},
        )
    )


async def create_auth_group_user_record(data, auth_group_name):
    auth_group_data = auth_group.get_auth_group(
        build_request(query_params={"name": auth_group_name})
    )
    group_data = group.get_group(
        build_request(
            query_params={"child_id": auth_group_data["id"], "type": "auth_group"}
        )
    )

    await group_user.create_group_user(
        build_request(
            method="POST",
            body={"group_id": group_data["id"], "user_id": data["user"]["id"]},
        )
    )


def create_new_student_record(data):
    response = requests.post(student_db_url, data=data, headers=db_request_token())
    if is_response_valid(response, "Student API could not post the data!"):
        created_student_data = is_response_empty(
            response.json(), "Student API could fetch the created student"
        )

        return created_student_data


def check_if_email_or_phone_is_part_of_request(query_params):
    if (
        "email" not in query_params
        or query_params["email"] == ""
        or query_params["email"] is None
    ) or (
        "phone" not in query_params
        or query_params["phone"] == ""
        or query_params["phone"] is None
    ):
        raise HTTPException(
            status_code=400, detail="Email/Phone is not part of the request data"
        )
    return


def check_if_student_id_is_part_of_request(query_params):
    if (
        "student_id" not in query_params
        or query_params["student_id"] == ""
        or query_params["student_id"] is None
    ):
        raise HTTPException(
            status_code=400, detail="Student ID is not part of the request data"
        )
    return


@router.get("/")
def get_students(request: Request):
    query_params = validate_and_build_query_params(
        request.query_params,
        STUDENT_QUERY_PARAMS + USER_QUERY_PARAMS + ENROLLMENT_RECORD_PARAMS,
    )
    response = requests.get(
        student_db_url, params=query_params, headers=db_request_token()
    )
    if is_response_valid(response, "Student API could not fetch the student!"):
        return is_response_empty(response.json(), True, "Student does not exist")


@router.get("/verify")
async def verify_student(request: Request, student_id: str):
    query_params = validate_and_build_query_params(
        request.query_params,
        STUDENT_QUERY_PARAMS + USER_QUERY_PARAMS + ["auth_group_id"],
    )

    response = requests.get(
        student_db_url,
        params={"student_id": student_id},
        headers=db_request_token(),
    )
    if is_response_valid(response):
        student_data = is_response_empty(response.json(), False)

        if student_data:
            student_data = student_data[0]
            for key, value in query_params.items():
                if key in USER_QUERY_PARAMS and student_data["user"].get(key) != value:
                    return False
                if key in STUDENT_QUERY_PARAMS and student_data.get(key) != value:
                    return False

                # check if the user belongs to the auth-group that sent the validation request
                if key == "auth_group_id":
                    response = group.get_group(
                        build_request(
                            query_params={
                                "child_id": query_params["auth_group_id"],
                                "type": "auth_group",
                            }
                        )
                    )
                    if response:
                        response = response[0]
                        group_user_response = group_user.get_group_user(
                            build_request(
                                query_params={
                                    "group_id": response["id"],
                                    "user_id": student_data["user"]["id"],
                                }
                            )
                        )
                        if not group_user_response:
                            return False
            return True

    return False


@router.post("/")
async def create_student(request: Request):
    data = await request.body()
    query_params = validate_and_build_query_params(
        data["form_data"],
        STUDENT_QUERY_PARAMS
        + USER_QUERY_PARAMS
        + ENROLLMENT_RECORD_PARAMS
        + SCHOOL_QUERY_PARAMS
        + ["id_generation"],
    )

    if not data["id_generation"]:
        student_id = query_params["student_id"]
        check_if_student_id_is_part_of_request(query_params)

        does_student_already_exist = await verify_student(
            build_request(), query_params["student_id"]
        )

        if does_student_already_exist:
            return query_params["student_id"]

    else:
        check_if_email_or_phone_is_part_of_request(query_params)

        user_already_exists = user.get_users(
            build_request(
                query_params={
                    "email": query_params["email"],
                    "phone": query_params["phone"],
                }
            )
        )
        if user_already_exists:
            response = get_students(
                build_request(query_params={"user_id": user_already_exists["user_id"]})
            )
            return response["student_id"]

        else:
            if data["auth_group"] == "JNVStudents":
                student_id = generate_JNV_student_id(data)

            student_id_already_exists = verify_student(build_request(), student_id=id)

            if student_id_already_exists:
                return student_id

    student_grade_id = grade.get_grade(
        build_request(query_params={"number": int(query_params["grade"])})
    )
    query_params["grade_id"] = student_grade_id["id"]

    new_student_data = create_new_student_record(query_params)

    await create_auth_group_user_record(new_student_data, data["auth_group"])

    if "school_name" in query_params:
        await create_school_user_record(new_student_data, query_params["school_name"])

    return student_id


# @router.post("/complete-profile-details")
# async def complete_profile_details(request: Request):
#     data = await request.json()

#     validate_and_build_query_params(
#         data,
#         STUDENT_QUERY_PARAMS
#         + USER_QUERY_PARAMS
#         + ENROLLMENT_RECORD_PARAMS,
#     )

#     user_data, student_data, enrollment_data = (
#         build_user_data(data),
#         build_student_data(data),
#         build_enrollment_data(data),
#     )

#     # get the PK of the student whose profile is being completed
#     student_response = get_students(
#         build_request(query_params={"student_id": data["student_id"]})
#     )

#     student_data["id"] = student_response[0]["id"]

#     # update the student with the entered details
#     await update_student(build_request(body=student_data))

#     user_data["id"] = student_response[0]["user"]["id"]

#     if len(user_data) > 0:
#         # update the student with the entered user details
#         await user.update_user(build_request(body=user_data))

#     # get the enrollment record of the student
#     enrollment_record_response = enrollment_record.get_enrollment_record(
#         build_request(query_params={"student_id": student_response[0]["id"]})
#     )

#     # if school name was entered by the student, get the school ID from the school table
#     if "school_name" in data:
#         school_response = school.get_school(
#             build_request(query_params={"name": data["school_name"]})
#         )
#         enrollment_data["school_id"] = school_response[0]["id"]

#     # if enrollment record already exists, update with new details
#     if enrollment_record_response != []:
#         enrollment_data["id"] = enrollment_record_response[0]["id"]

#         enrollment_record_response = await enrollment_record.update_enrollment_record(
#             build_request(body=enrollment_data)
#         )

#     # else, create a new enrollment record for the student
#     else:
#         enrollment_data["student_id"] = student_response[0]["id"]

#         enrollment_record_response = await enrollment_record.create_enrollment_record(
#             build_request(body=enrollment_data)
#         )

# def build_enrollment_data(data):
#     enrollment_data = {}
#     for key in data.keys():
#         if key in ENROLLMENT_RECORD_PARAMS and key != "student_id":
#             enrollment_data[key] = data[key]
#     return enrollment_data


# def build_student_data(data):
#     student_data = {}
#     for key in data.keys():
#         if key in STUDENT_QUERY_PARAMS:
#             student_data[key] = data[key]
#     return student_data


# def build_user_data(data):
#     user_data = {}
#     for key in data.keys():
#         if key in USER_QUERY_PARAMS:
#             user_data[key] = data[key]
#     return user_data
