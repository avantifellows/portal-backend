from pydantic import BaseSettings
from fastapi_jwt_auth import AuthJWT


class Settings(BaseSettings):
    jwt_secret_key: str = "secret"


@AuthJWT.load_config
def get_config():
    return Settings()
