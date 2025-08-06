from pydantic import BaseModel
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
    TOKEN: str = os.environ.get("DB_SERVICE_TOKEN")
    SQS_ACCESS_KEY: str = os.environ.get("SQS_ACCESS_KEY")
    SQS_SECRET_ACCESS_KEY: str = os.environ.get("SQS_SECRET_ACCESS_KEY")
    AWS_SQS_URL: str = os.environ.get("AWS_SQS_URL")

    # Business logic configuration
    DEFAULT_ACADEMIC_YEAR: str = os.environ.get("DEFAULT_ACADEMIC_YEAR", "2025-2026")


# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


settings = Settings()
