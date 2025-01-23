from pydantic import BaseModel
from typing import Union, Dict, Optional


class AuthGroupResponse(BaseModel):
    id: str
    name: str
    input_schema: Optional[Dict] = {}
    locale: Optional[str] = ""
    locale_data: Optional[Dict] = {}


class AuthUser(BaseModel):
    id: str
    type: str
    name: Optional[str] = None
    is_user_valid: Optional[bool] = None
    data: Union[Dict[str, str], None]


class BatchResponse(BaseModel):
    id: str
    name: str
    contact_hours_per_week: Optional[int] = None
    batch_id: str
    parent_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    program_id: Optional[int] = None
    auth_group_id: Optional[int] = None


class EnrollmentRecordResponse(BaseModel):
    id: str
    academic_year: str
    is_current: bool
    start_date: str
    end_date: Optional[str] = None
    group_id: int
    group_type: str
    user_id: int
    subject_id: int


class SessionResponse(BaseModel):
    id: Optional[str] = None
    session_id: Optional[str] = None
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    platform: Optional[str] = None
    platform_link: Optional[str] = None
    purpose: Optional[Dict] = {}
    meta_data: Optional[Dict] = {}
    platform_id: Optional[str] = None
    is_session_open: bool
    type: Optional[str] = None
    auth_type: Optional[str] = None
    signup_form: Optional[str] = None
    id_generation: Optional[str] = None
    redirection: Optional[str] = None
    popup_form: Optional[str] = None
    signup_form_id: Optional[str] = None
    popup_form_id: Optional[str] = None
    session_occurrence_id: Optional[str] = None


class UserSession(BaseModel):
    user_id: str
    session_id: str
    session_occurrence_id: int
    user_activity_type: str
    user_type: str
    data: Optional[Dict] = {}
