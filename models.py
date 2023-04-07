from pydantic import BaseModel
from typing import Union, Dict, Optional


class User(BaseModel):
    id: str
    is_user_valid: bool
    data: Union[Dict[str, str], None]


class GroupResponse(BaseModel):
    id: str
    name: str
    input_schema: Dict
    locale: str = "default"
    locale_data: Dict
    auth_type: Optional[str] = ""
