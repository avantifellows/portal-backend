from pydantic import BaseModel
from typing import Union, Dict


class User(BaseModel):
    id: str
    is_user_valid: bool
    data: Union[Dict[str, str], None]
