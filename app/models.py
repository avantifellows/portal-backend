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
    purpose: Optional[Dict] = {}
    meta_data: Optional[Dict] = {}
    platform_id: Optional[str] = None
    is_session_open: bool
    type: Optional[str] = None
    auth_type: Optional[str] = None
    activate_signup: Optional[str] = None
    id_generation: Optional[str] = None
    redirection: Optional[str] = None
    pop_up_form: Optional[str] = None


class GroupResponse(BaseModel):
    id: str
    name: str
    input_schema: Optional[Dict] = {}
    locale: Optional[str] = ""
    locale_data: Optional[Dict] = {}


class UserSession(BaseModel):
    user_id: str
    session_occurrence_id: int
    is_user_valid: bool
    data: Optional[Dict] = {}
