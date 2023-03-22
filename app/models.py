from pydantic import BaseModel
from typing import Union, Dict, Optional


class AuthUser(BaseModel):
    id: str
    type: str
    name: Optional[str] = None
    is_user_valid: Optional[bool] = None
    data: Union[Dict[str, str], None]


class SessionResponse(BaseModel):
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
    name: str
    group_input_schema: Optional[Dict] = {}
    group_locale: Optional[str] = ""
    group_locale_data: Optional[Dict] = {}
    auth_type: Optional[str] = ""
