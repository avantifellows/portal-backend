from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from services.sashakt_service import create_sashakt_launch

router = APIRouter(prefix="/sashakt", tags=["Sashakt"])


class SashaktLaunchRequest(BaseModel):
    user_id: str
    test_link_uuid: Optional[str] = None
    redirect_id: Optional[str] = None
    device_info: Optional[str] = None

    class Config:
        extra = "forbid"


@router.post("/launch")
async def launch_sashakt_test(payload: SashaktLaunchRequest):
    return create_sashakt_launch(payload.dict(exclude_none=True))
