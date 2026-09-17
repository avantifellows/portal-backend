"""Server-side check of an OTP against the OTP lambda."""

import json
import requests
from settings import settings
from logger_config import get_logger

logger = get_logger()

OTP_OK = 200
OTP_UNAVAILABLE = 0


def verify_otp(phone: str, code: str) -> int:
    """Return the OTP service status code; 200 means the code matched."""
    base = (settings.OTP_SERVICE_URL or "").rstrip("/")
    if not base:
        logger.error("OTP_SERVICE_URL is not configured")
        return OTP_UNAVAILABLE
    try:
        response = requests.post(
            f"{base}/verifyotp", params={"phone": phone, "code": code}, timeout=10
        )
        data = response.json()
        if isinstance(data, str):
            data = json.loads(data)
        return int(data.get("statusCode", OTP_UNAVAILABLE))
    except Exception as e:
        logger.error(f"OTP verification failed: {e}")
        return OTP_UNAVAILABLE
