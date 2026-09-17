from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import AuthUser, LaunchTokenRequest
from services.token_service import (
    ALLOWED_SESSION_MODES,
    LAUNCH_AUDIENCES,
    LAUNCH_SESSION_MODE,
    PERSISTENT_SESSION_MODE,
    encode,
    issue_launch_token,
    issue_session_tokens,
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


@router.post("/create-access-token")
def create_access_token(auth_user: AuthUser):
    session_mode = auth_user.session_mode or PERSISTENT_SESSION_MODE
    data = {k: v for k, v in (auth_user.data or {}).items() if v is not None}

    if session_mode not in ALLOWED_SESSION_MODES:
        raise HTTPException(
            status_code=400,
            detail="Invalid session_mode. Must be 'persistent' or 'launch'",
        )

    if auth_user.type not in ["user", "organization"]:
        raise HTTPException(
            status_code=400, detail="Invalid type. Must be 'user' or 'organization'"
        )

    if auth_user.type == "organization":
        if not auth_user.name:
            return HTTPException(
                status_code=400, detail="Data Parameter {} is missing!".format("name")
            )
        payload = {
            "sub": auth_user.id,
            "name": auth_user.name,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(weeks=260),
        }
        return {
            "access_token": encode(payload),
            "refresh_token": "",
            "session_mode": session_mode,
        }

    return issue_session_tokens(
        subject=auth_user.id,
        data=data,
        session_mode=session_mode,
        audience=auth_user.audience,
        with_refresh=bool(auth_user.is_user_valid),
    )


@router.post("/launch-token")
def create_launch_token(
    request: LaunchTokenRequest, payload: dict = Depends(verify_jwt)
):
    if payload.get("type") == "refresh":
        raise HTTPException(status_code=401, detail="Access token required")
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
