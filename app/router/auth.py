from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from models import AuthUser
import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/")
def index():
    return "Portal Authentication!"


# if user is valid, generates both access token and refresh token. Otherwise, only an access token.
@router.post("/create-access-token")
def create_access_token(auth_user: AuthUser, Authorize: AuthJWT = Depends()):
    refresh_token = ""
    data = auth_user.data

    if auth_user.data is None:
        data = {}

    if auth_user.type == "organization":
        if not auth_user.name:
            return HTTPException(
                status_code=400, detail="Data Parameter {} is missing!".format("name")
            )
        expires = datetime.timedelta(weeks=260)
        access_token = Authorize.create_access_token(
            subject=auth_user.id,
            user_claims={"name": auth_user.name},
            expires_time=expires,
        )

    elif auth_user.type == "user":
        if "is_user_valid" not in auth_user.dict().keys():
            return HTTPException(
                status_code=400,
                detail="Data Parameter {} is missing!".format("is_user_valid"),
            )
        if auth_user.is_user_valid:
            refresh_token = Authorize.create_refresh_token(
                subject=auth_user.id, user_claims=data
            )
        access_token = Authorize.create_access_token(
            subject=auth_user.id, user_claims=data
        )

    return {"access_token": access_token, "refresh_token": refresh_token}


# generates refresh token
@router.post("/refresh-token")
def refresh_token(Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()
    current_user = Authorize.get_jwt_subject()
    data = Authorize.get_raw_jwt()
    new_access_token = Authorize.create_access_token(subject=current_user, user_claims=data)
    return {"access_token": new_access_token}


# verifies token
@router.get("/verify")
def verify_token(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    current_user = Authorize.get_jwt_subject()
    data = Authorize.get_raw_jwt()
    return {"id": current_user, "data": data}


@router.delete("/logout")
def logout(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    Authorize.unset_jwt_cookies()
    return {"message": "Successful logout"}
