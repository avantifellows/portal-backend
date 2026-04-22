from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import AuthUser
import datetime
import jwt
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

# JWT bearer for token extraction
security = HTTPBearer()
PERSISTENT_SESSION_MODE = "persistent"
LAUNCH_SESSION_MODE = "launch"
ALLOWED_SESSION_MODES = {PERSISTENT_SESSION_MODE, LAUNCH_SESSION_MODE}


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token and return payload with proper error handling
    """
    try:
        payload = jwt.decode(
            credentials.credentials, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=422, detail="Signature has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/")
def index():
    return "Portal Authentication!"


def _build_access_payload(
    auth_user: AuthUser, data: dict, expires_in: datetime.timedelta
) -> dict:
    payload = {
        "sub": auth_user.id,
        "exp": datetime.datetime.utcnow() + expires_in,
        **data,
    }

    session_mode = auth_user.session_mode or PERSISTENT_SESSION_MODE
    payload["session_mode"] = session_mode
    payload["persist"] = session_mode == PERSISTENT_SESSION_MODE

    if auth_user.audience:
        payload["aud"] = auth_user.audience

    return payload


# if user is valid, generates both access token and refresh token. Otherwise, only an access token.
@router.post("/create-access-token")
def create_access_token(auth_user: AuthUser):
    access_token = ""
    refresh_token = ""
    data = auth_user.data
    session_mode = auth_user.session_mode or PERSISTENT_SESSION_MODE

    if auth_user.data is None:
        data = {}
    else:
        data = {k: v for k, v in auth_user.data.items() if v is not None}

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
        expires = datetime.timedelta(weeks=260)
        payload = {
            "sub": auth_user.id,
            "name": auth_user.name,
            "exp": datetime.datetime.utcnow() + expires,
        }
        access_token = jwt.encode(
            payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
        )

    elif auth_user.type == "user":
        if "is_user_valid" not in auth_user.dict().keys():
            return HTTPException(
                status_code=400,
                detail="Data Parameter {} is missing!".format("is_user_valid"),
            )

        access_expires_in = (
            datetime.timedelta(minutes=15)
            if session_mode == LAUNCH_SESSION_MODE
            else datetime.timedelta(hours=1)
        )

        access_payload = _build_access_payload(auth_user, data, access_expires_in)
        access_token = jwt.encode(
            access_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
        )

        # Create refresh token only for persistent user sessions
        if auth_user.is_user_valid and session_mode == PERSISTENT_SESSION_MODE:
            refresh_payload = {
                "sub": auth_user.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
                "type": "refresh",
                **data,
            }
            refresh_token = jwt.encode(
                refresh_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
            )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "session_mode": session_mode,
    }


# generates refresh token
@router.post("/refresh-token")
def refresh_token(payload: dict = Depends(verify_jwt)):
    # Check if this is a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    current_user = payload.get("sub")

    # Create custom claims from old token
    custom_claims = {
        key: value
        for key, value in payload.items()
        if key not in {"sub", "exp", "type", "iat"}
    }

    # Create new access token
    new_payload = {
        "sub": current_user,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        **custom_claims,
    }
    new_access_token = jwt.encode(
        new_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
    )

    return {"access_token": new_access_token}


# verifies token
@router.get("/verify")
def verify_token(payload: dict = Depends(verify_jwt)):
    current_user = payload.get("sub")
    return {"id": current_user, "data": payload}


@router.delete("/logout")
def logout(payload: dict = Depends(verify_jwt)):
    # With JWT, logout is typically handled client-side by removing the token
    # For server-side logout, you'd need to maintain a blacklist
    return {"message": "Successful logout"}
