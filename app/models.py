from pydantic import BaseModel
from typing import Union, Dict, Optional


class AuthUser(BaseModel):
    id: str
    type: str
    name: Optional[str] = None
    is_user_valid: Optional[bool] = None
    data: Union[Dict[str, str], None]


class SessionResponse(BaseModel):
    id: Optional[str] = None
    session_id: Optional[str] = None
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    platform: Optional[str] = None
    platform_link: Optional[str] = None
    purpose: Optional[str] = None
    meta_data: Optional[Dict] = {}
    platform_id: Optional[str] = None
    is_session_open: bool


class GroupResponse(BaseModel):
    id: str
    name: str
    group_input_schema: Optional[Dict] = {}
    group_locale: Optional[str] = ""
    group_locale_data: Optional[Dict] = {}
    auth_type: Optional[str] = ""


class UserSession(BaseModel):
    user_id: int
    session_occurrence_id: int
    is_user_valid: bool
    data: Optional[Dict] = {}
