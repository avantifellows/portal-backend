AUTH_GROUP_QUERY_PARAMS = ["id", "name", "locale"]

BATCH_QUERY_PARAMS = [
    "id",
    "name",
    "contact_hours_per_week",
    "batch_id",
    "parent_id",
    "program_id",
    "auth_group_id",
]

ENROLLMENT_RECORD_PARAMS = [
    "academic_year",
    "is_current",
    "start_date",
    "end_date",
    "group_id",
    "group_type",
    "user_id",
    "subject_id",
]

FORM_SCHEMA_QUERY_PARAMS = ["id", "name", "attributes"]

GROUP_QUERY_PARAMS = ["id", "type", "child_id"]

GROUP_USER_QUERY_PARAMS = ["id", "group_id", "user_id"]

SCHOOL_QUERY_PARAMS = [
    "id",
    "name",
    "school_name",
    "code",
    "board_medium",
    "region",
    "district",
    "state",
    "block_name",
]

SESSION_QUERY_PARAMS = ["id", "name", "session_id"]

STUDENT_QUERY_PARAMS = [
    "student_id",
    "apaar_id",
    "grade",
    "grade_id",
    "father_name",
    "father_phone",
    "mother_name",
    "mother_phone",
    "category",
    "stream",
    "board_stream",
    "planned_competitive_exams",
    "family_income",
    "father_profession",
    "father_education_level",
    "mother_profession",
    "mother_education_level",
    "time_of_device_availability",
    "has_internet_access",
    "primary_smartphone_owner",
    "primary_smartphone_owner_profession",
    "guardian_name",
    "guardian_relation",
    "guardian_phone",
    "guardian_education_level",
    "guardian_profession",
    "has_category_certificate",
    "category_certificate",
    "physically_handicapped",
    "physically_handicapped_certificate",
    "annual_family_income",
    "monthly_family_income",
    "number_of_smartphones",
    "family_type",
    "number_of_four_wheelers",
    "number_of_two_wheelers",
    "goes_for_tuition_or_other_coaching",
    "know_about_avanti",
    "percentage_in_grade_10_science",
    "percentage_in_grade_10_math",
    "percentage_in_grade_10_english",
    "grade_10_marksheet",
    "photo",
    "school_medium",
]

TEACHER_QUERY_PARAMS = ["teacher_id", "subject", "designation", "subject_id"]

CANDIDATE_QUERY_PARAMS = [
    "candidate_id",
    "degree",
    "college_name",
    "branch_name",
    "latest_cgpa",
    "subject",
]

USER_QUERY_PARAMS = [
    "id",
    "first_name",
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
]

authgroup_state_mapping = {
    "HaryanaStudents": "Haryana",
    "DelhiStudents": "Delhi",
    "UttarakhandStudents": "Uttarakhand",
    "GujaratStudents": "Gujarat",
    "HimachalStudents": "Himachal Pradesh",
    "PunjabStudents": "Punjab",
    "MaharashtraStudents": "Maharashtra",
    "TNStudents": "Tamil Nadu",
    "PunjabTeachers": "Punjab",
    "TNTeachers": "Tamil Nadu",
    "ChhattisgarhStudents": "Chhattisgarh",
}

# Reverse mapping for state to authgroup lookup
state_authgroup_mapping = {v: k for k, v in authgroup_state_mapping.items()}
