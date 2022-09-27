from fastapi import APIRouter, Depends
from fastapi_jwt_auth import AuthJWT
from models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


# if user is valid, generates both access token and refresh token. Otherwise, only an access token.
@router.post("/create_access_token")
def create_access_token(user: User, Authorize: AuthJWT = Depends()):
    data = user.data
    if user.data is None:
        data = {}
    if user.is_user_valid:
        access_token = Authorize.create_access_token(
            subject=user.id, user_claims=data)
        refresh_token = Authorize.create_refresh_token(
            subject=user.id, user_claims=data)
        print("hello")
        Authorize.set_access_cookies(access_token)
        Authorize.set_refresh_cookies(refresh_token)
        return {"message": "Successful login"}
    access_token = Authorize.create_access_token(
        subject=user.id, user_claims=data)
    Authorize.set_access_cookies(access_token)
    return {"message": "Successful login"}


# generates refresh token
@router.post("/refresh_token")
def refresh_token(Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()
    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)
    Authorize.set_access_cookies(new_access_token)
    return {"message": "Token has been refreshed"}


# example ->  protected method
@router.get('/user')
def user(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    current_user = Authorize.get_jwt_subject()
    return {"user": current_user}
