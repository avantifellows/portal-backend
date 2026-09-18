from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import LaunchTokenRequest
from services.token_service import (
    LAUNCH_AUDIENCES,
    LAUNCH_SESSION_MODE,
    encode,
    is_launch_allowed,
    issue_launch_token,
)
import datetime
import jwt
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

security = HTTPBearer()


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=422, detail="Signature has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/")
def index():
    return "Portal Authentication!"


def require_session(payload: dict = Depends(verify_jwt)) -> dict:
    """Any live access token (not a refresh token)."""
    if payload.get("type") == "refresh":
        raise HTTPException(status_code=401, detail="Access token required")
    return payload


def require_validated_session(payload: dict = Depends(require_session)) -> dict:
    """An access token whose login was fully verified (OTP done, not a testing id)."""
    if not payload.get("user_validated", True):
        raise HTTPException(status_code=401, detail="Session not validated")
    return payload


def session_user_id(payload: dict) -> str:
    return str(payload.get("user_id") or payload.get("sub"))


@router.post("/launch-token")
def create_launch_token(
    request: LaunchTokenRequest, payload: dict = Depends(require_session)
):
    if not is_launch_allowed(payload):
        raise HTTPException(status_code=401, detail="Session not validated")
    if request.audience not in LAUNCH_AUDIENCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audience. Must be one of {sorted(LAUNCH_AUDIENCES)}",
        )
    return {
        "access_token": issue_launch_token(payload, request.audience),
        "session_mode": LAUNCH_SESSION_MODE,
    }


@router.post("/refresh-token")
def refresh_token(payload: dict = Depends(verify_jwt)):
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    current_user = payload.get("sub")
    custom_claims = {
        key: value
        for key, value in payload.items()
        if key not in {"sub", "exp", "type", "iat"}
    }
    new_payload = {
        "sub": current_user,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        **custom_claims,
    }
    return {"access_token": encode(new_payload)}


@router.get("/verify")
def verify_token(payload: dict = Depends(verify_jwt)):
    current_user = payload.get("sub")
    return {"id": current_user, "data": payload}


@router.delete("/logout")
def logout(payload: dict = Depends(verify_jwt)):
    return {"message": "Successful logout"}
