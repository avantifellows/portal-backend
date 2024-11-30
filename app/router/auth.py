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
    # Define access_token and refresh_token as empty strings
    access_token = ""
    refresh_token = ""
    data = auth_user.data if auth_user.data is not None else {}

    # Validate auth_user.type
    if auth_user.type not in ["user", "organization"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid user type! Must be either 'user' or 'organization'.",
        )

    if auth_user.type == "organization":
        if not auth_user.name:
            raise HTTPException(
                status_code=400, detail="Data Parameter 'name' is missing!"
            )
        expires = datetime.timedelta(weeks=260)
        access_token = Authorize.create_access_token(
            subject=auth_user.id,
            user_claims={"name": auth_user.name},
            expires_time=expires,
        )

    elif auth_user.type == "user":
        if "is_user_valid" not in auth_user.dict().keys():
            raise HTTPException(
                status_code=400, detail="Data Parameter 'is_user_valid' is missing!"
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
    old_data = Authorize.get_raw_jwt()
    custom_claims = {"group": old_data.get("group", {})}
    new_access_token = Authorize.create_access_token(
        subject=current_user, user_claims=custom_claims
    )
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
