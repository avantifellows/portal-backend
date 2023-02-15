from pydantic import BaseModel
from typing import Union, Dict, Optional


class User(BaseModel):
    id: str
    is_user_valid: bool
    data: Union[Dict[str, str], None]


class Student(BaseModel):
    father_name: Optional[str] = None
    father_phone_number: Optional[str] = None
    mother_name: Optional[str] = None
    mother_phone_number: Optional[str] = None
    category: Optional[str] = None
    stream: Optional[str] = None
    physically_handicapped: Optional[str] = None
    family_income: Optional[int] = None
    father_profession: Optional[str] = None
    father_educational_level: Optional[str] = None
    mother_profession: Optional[str] = None
    mother_educational_level: Optional[str] = None
    time_of_device_availability: Optional[str] = None
    has_internet_access: Optional[str] = None
    contact_hours_per_week: Optional[str] = None
    is_dropper: Optional[bool] = None


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
