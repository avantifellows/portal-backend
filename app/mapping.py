FORM_GROUP_MAPPING = {
    "HaryanaStudents": "Haryana Student Profile",
    "EnableStudents": "Enable Student Profile",
}

STUDENT_QUERY_PARAMS = [
    "student_id",
    "category",
    "stream",
    "physically_handicapped",
    "annual_family_income",
    "monthly_family_income",
    "father_name",
    "father_phone",
    "father_profession",
    "father_education_level",
    "mother_name",
    "mother_phone",
    "mother_profession",
    "mother_education_level",
    "time_of_device_availability",
    "has_internet_access",
    "primary_smartphone_owner",
    "primary_smartphone_owner_profession",
    "group",
    "planned_competitive_exams",
    #    "region",
    "user_id",
    "primary_contact",
    "guardian_name",
    "guardian_relation",
    "guardian_phone",
    "guardian_education_level",
    "guardian_profession",
    "know_about_avanti",
]

TEACHER_QUERY_PARAMS = ["grade", "designation"]

USER_QUERY_PARAMS = [
    "id",
    "first_name",
    "middle_name",
    "last_name",
    "email",
    "phone",
    "whatsapp_phone",
    "gender",
    "address",
    "city",
    "district",
    "state",
    "pincode",
    "role",
    "date_of_birth",
    "country",
    "consent_check",
]

ENROLLMENT_RECORD_PARAMS = [
    "grade",
    "academic_year",
    "student_id",
    "school_id",
    "school_name",
    "is_current",
    "board_medium",
    "date_of_enrollment",
]

SCHOOL_QUERY_PARAMS = ["id", "name", "code", "state", "district"]
GROUP_TYPE_QUERY_PARAMS = ["id", "type", "child_id"]
GROUP_QUERY_PARAMS = ["name", "id", "locale"]
STUDENT_EXAM_RECORD_QUERY_PARAMS = [
    "student_id",
    "exam_id",
    "application_number",
    "application_password",
    "date",
    "score",
    "rank",
]
