from pydantic import BaseModel
from fastapi_jwt_auth import AuthJWT
from dotenv import load_dotenv
import os

load_dotenv()


# 'authjwt_secret_key' stores the secret key for encoding and decoding
class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY")


# callback to get the configuration
@AuthJWT.load_config
def get_config():
    return Settings()


settings = Settings()
