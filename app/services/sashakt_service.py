from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests
from fastapi import HTTPException

from helpers import is_response_valid
from logger_config import get_logger
from settings import settings

logger = get_logger()


def _get_sashakt_auth_headers() -> Dict[str, str]:
    if (
        not settings.SASHAKT_API_URL
        or not settings.SASHAKT_ADMIN_EMAIL
        or not settings.SASHAKT_ADMIN_PASSWORD
    ):
        raise HTTPException(status_code=500, detail="Sashakt launch is not configured")

    response = requests.post(
        f"{settings.SASHAKT_API_URL.rstrip('/')}/login/access-token",
        data={
            "username": settings.SASHAKT_ADMIN_EMAIL,
            "password": settings.SASHAKT_ADMIN_PASSWORD,
        },
    )
    if not is_response_valid(response, "Sashakt authentication failed"):
        raise HTTPException(status_code=500, detail="Sashakt authentication failed")

    access_token = response.json().get("access_token")
    if not access_token:
        raise HTTPException(status_code=500, detail="Sashakt authentication failed")
    return {"Authorization": f"Bearer {access_token}"}


def _provision_sashakt_candidate(
    external_identifier: str,
    test_link_uuid: str,
    device_info: Optional[str],
) -> Dict[str, Any]:
    if not settings.SASHAKT_API_URL:
        raise HTTPException(status_code=500, detail="Sashakt launch is not configured")

    payload: Dict[str, Any] = {
        "test_link_uuid": test_link_uuid,
        "external_identifier": external_identifier,
    }
    if device_info:
        payload["device_info"] = device_info

    response = requests.post(
        f"{settings.SASHAKT_API_URL.rstrip('/')}/candidate/external/provision",
        json=payload,
        headers=_get_sashakt_auth_headers(),
    )
    if is_response_valid(response, "Sashakt could not provision the candidate"):
        return response.json()
    raise HTTPException(status_code=500, detail="Sashakt provisioning failed")


def _build_launch_url(test_link_uuid: str, candidate_uuid: str) -> str:
    base_url = settings.SASHAKT_WEBAPP_URL.rstrip("/")
    if not base_url:
        raise HTTPException(
            status_code=500, detail="Sashakt webapp URL is not configured"
        )

    query = urlencode({"candidate_uuid": candidate_uuid})
    return f"{base_url}/test/{test_link_uuid}?{query}"


def create_sashakt_launch(data: Dict[str, Any]) -> Dict[str, Any]:
    external_identifier = str(data.get("user_id") or "")
    test_link_uuid = str(data.get("test_link_uuid") or data.get("redirect_id") or "")

    if not external_identifier or not test_link_uuid:
        raise HTTPException(
            status_code=400, detail="user_id and test_link_uuid are required"
        )

    # Sashakt owns the candidate mapping: it looks up-or-creates a single
    # candidate per (organization, external_identifier), so re-launching the same
    # user is idempotent server-side. Portal stores no mapping of its own. The
    # attempt itself is created when the candidate starts the test.
    provisioned = _provision_sashakt_candidate(
        external_identifier=external_identifier,
        test_link_uuid=test_link_uuid,
        device_info=data.get("device_info"),
    )

    candidate_uuid = provisioned["candidate_uuid"]

    return {
        "launch_url": _build_launch_url(test_link_uuid, candidate_uuid),
        "candidate_uuid": candidate_uuid,
    }
