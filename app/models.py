from pydantic import BaseModel
from typing import Union, Dict, Optional


class User(BaseModel):
    id: str
    is_user_valid: bool
    data: Union[Dict[str, str], None]

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
    purpose: Optional[str] = None
    meta_data: Optional[Dict] = {}