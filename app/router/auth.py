from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from models import User
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/")
def index():
    return "Portal Authentication!"


# if user is valid, generates both access token and refresh token. Otherwise, only an access token.
@router.post("/create-access-token")
def create_access_token(user: User, Authorize: AuthJWT = Depends()):
    refresh_token = ""
    if user.type == "organization":
        if not user.name:
            return HTTPException(
                status_code=400, detail="Data Parameter {} is missing!".format("name")
            )
        expires = datetime.timedelta(years=5)
        access_token = Authorize.create_access_token(
            subject=user.id, user_claims={"name": user.name}, expires_time=expires
        )

    elif user.type == "user":
        if "is_user_valid" not in user:
            return HTTPException(
                status_code=400,
                detail="Data Parameter {} is missing!".format("is_user_valid"),
            )
        if user.is_user_valid:
            refresh_token = Authorize.create_refresh_token(
                subject=user.id, user_claims=user.data
            )
        access_token = Authorize.create_access_token(
            subject=user.id, user_claims=user.data
        )

    return {"access_token": access_token, "refresh_token": refresh_token}


# generates refresh token
@router.post("/refresh-token")
def refresh_token(Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()
    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)
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
