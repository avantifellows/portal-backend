from pydantic import BaseModel
from typing import Union, Dict, Optional


class User(BaseModel):
    id: str
    is_user_valid: bool
    data: Union[Dict[str, str], None]


class SessionOpenResponse(BaseModel):
    id: str
    session_id: str
    name: Optional[str] = None
    is_active: bool
    start_time:  Optional[str] = None
    end_time:  Optional[str] = None
    repeat_schedule:  Optional[str] = None
    platform:  Optional[str] = None
    platform_link:  Optional[str] = None
    purpose:  Optional[str] = None
    meta_data: Optional[Dict] = {}
    platform_id:  Optional[str] = None
    is_session_open: bool

class SessionCloseResponse(BaseModel):
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
    start_time: str
    end_time: Optional[str] = ""
    data: Optional[Dict] = {}