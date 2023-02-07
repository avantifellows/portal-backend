from pydantic import BaseModel
from typing import Union, Dict, Optional


class User(BaseModel):
    id: str
    is_user_valid: bool
    data: Union[Dict[str, str], None]


class StudentRequest(BaseModel):
    id: str
    stream: Optional[str]


class Student(BaseModel):
    student_id: Optional[str] = ""
    father_name: Optional[str] = ""
    father_phone_number: Optional[str] = ""
    mother_name: Optional[str] = ""
    mother_phone_number: Optional[str] = ""
    category: Optional[str] = ""
    stream: Optional[str] = ""
    physically_handicapped: Optional[str] = ""
    family_income: Optional[int] = ""
    father_profession: Optional[str] = ""
    father_educational_level: Optional[str] = ""
    mother_profession: Optional[str] = ""
    mother_educational_level: Optional[str] = ""
    time_of_device_availability: Optional[str] = ""
    has_internet_access: Optional[str] = ""
    contact_hours_per_week: Optional[str] = ""
    is_dropper: Optional[bool] = ""


class SessionResponse(BaseModel):
    id: str
    session_id: str
    name: Optional[str] = None
    is_active: bool
    start_time: str
    end_time: str
    repeat_schedule: str
    platform: str
    platform_link: str
    purpose: str
    meta_data: Optional[Dict] = {}


class GroupResponse(BaseModel):
    id: str
    name: str
    group_input_schema: Optional[Dict] = {}
    group_locale: Optional[str] = ""
    group_locale_data: Optional[Dict] = {}
    auth_type: Optional[str] = ""
