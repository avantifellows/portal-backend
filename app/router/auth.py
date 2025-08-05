from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import AuthUser
import datetime
import jwt
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

# JWT bearer for token extraction
security = HTTPBearer()


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


# if user is valid, generates both access token and refresh token. Otherwise, only an access token.
@router.post("/create-access-token")
def create_access_token(auth_user: AuthUser):
    access_token = ""
    refresh_token = ""
    data = auth_user.data

    if auth_user.data is None:
        data = {}

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

        # Create access token
        access_payload = {
            "sub": auth_user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            **data,
        }
        access_token = jwt.encode(
            access_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
        )

        # Create refresh token if user is valid
        if auth_user.is_user_valid:
            refresh_payload = {
                "sub": auth_user.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
                "type": "refresh",
                **data,
            }
            refresh_token = jwt.encode(
                refresh_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256"
            )

    return {"access_token": access_token, "refresh_token": refresh_token}


# generates refresh token
@router.post("/refresh-token")
def refresh_token(payload: dict = Depends(verify_jwt)):
    # Check if this is a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    current_user = payload.get("sub")

    # Create custom claims from old token
    custom_claims = {}
    if "group" in payload:
        custom_claims = {"group": payload["group"]}

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
