from pydantic import BaseModel
from fastapi_jwt_auth import AuthJWT
import os

if "JWT_SECRET_KEY" not in os.environ:
    from dotenv import load_dotenv

    load_dotenv("../.env")


# 'authjwt_secret_key' stores the secret key for encoding and decoding
class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    authjwt_token_location: set = {"headers"}
    # Allow JWT cookies to be sent over https only
    authjwt_cookie_secure: bool = False
    # Enable csrf double submit protection.
    authjwt_cookie_csrf_protect: bool = False
    # makes your website more secure from CSRF Attacks
    authjwt_cookie_samesite: str = "lax"
    # DB service base URL
    db_url: str = os.environ.get("DB_SERVICE_URL")
    token: str = os.environ.get("DB_SERVICE_TOKEN")
    print("here":token)


# callback to get the configuration
@AuthJWT.load_config
def get_config():
    return Settings()


settings = Settings()
