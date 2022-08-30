from fastapi import APIRouter, Depends
from fastapi_jwt_auth import AuthJWT
from typing import Union, Dict

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/create_access_token")
def create_access_token(id: str, data: Union[Dict[str, str], None], is_valid: bool, Authorize: AuthJWT = Depends()):
    if is_valid:
        access_token = Authorize.create_access_token(
            subject=id, user_claims=data)
        refresh_token = Authorize.create_refresh_token(
            subject=id, user_claims=data)
        return {"access_token:", access_token, "refresh_token:", refresh_token}
    access_token = Authorize.create_access_token(subject=id, user_claims=data)
    return access_token


@router.post("/refresh_token")
def refresh_token(Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()
    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)
    return {"access_token": new_access_token}
