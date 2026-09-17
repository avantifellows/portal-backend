"""Server-side minting of portal session and launch tokens."""

import datetime
import os
from typing import Any, Dict, Optional

import jwt

from logger_config import get_logger
from services.auth_group_service import get_auth_group

logger = get_logger()

ALGORITHM = "HS256"
PERSISTENT_SESSION_MODE = "persistent"
LAUNCH_SESSION_MODE = "launch"
ALLOWED_SESSION_MODES = {PERSISTENT_SESSION_MODE, LAUNCH_SESSION_MODE}
LAUNCH_AUDIENCES = {"quiz", "report", "form"}
TESTING_AUTH_GROUPS = {"AFTesting"}

ACCESS_TOKEN_TTL = datetime.timedelta(hours=1)
LAUNCH_TOKEN_TTL = datetime.timedelta(minutes=15)
REFRESH_TOKEN_TTL = datetime.timedelta(days=30)

RESERVED_CLAIMS = {"sub", "exp", "iat", "aud", "type", "session_mode", "persist"}

USER_FIELDS = [
    "first_name",
    "last_name",
    "name",
    "phone",
    "email",
    "gender",
    "date_of_birth",
]
STUDENT_FIELDS = [
    "student_id",
    "apaar_id",
    "grade_id",
    "grade",
    "stream",
    "status",
    "g12_graduating_year",
    "school_id",
    "school_code",
    "school_name",
]
TEACHER_FIELDS = [
    "teacher_id",
    "designation",
    "subject_id",
    "subject",
    "is_af_teacher",
    "school_id",
    "school_code",
    "school_name",
]
CANDIDATE_FIELDS = [
    "candidate_id",
    "subject_id",
    "subject",
    "degree",
    "college_name",
    "branch_name",
]
SCHOOL_FIELDS = [
    "school_code",
    "code",
    "school_name",
    "name",
    "udise_code",
    "state",
    "district",
    "region",
    "block_name",
]
IDENTIFIER_KEYS = [
    "student_id",
    "apaar_id",
    "teacher_id",
    "candidate_id",
    "school_code",
    "code",
]


def _secret() -> str:
    return os.getenv("JWT_SECRET_KEY")


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _str_or_none(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    return str(value)


def _pick(source: Dict[str, Any], keys) -> Optional[Dict[str, Any]]:
    picked = {
        key: source[key]
        for key in keys
        if source.get(key) is not None and source.get(key) != ""
    }
    return picked or None


def _first(source: Dict[str, Any], keys) -> Any:
    for key in keys:
        value = source.get(key)
        if value is not None and value != "":
            return value
    return None


def resolve_auth_group(
    auth_group: Optional[str] = None, auth_group_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Look up the auth group by name or id; None when neither resolves."""
    try:
        if auth_group:
            return get_auth_group(name=auth_group)
        if auth_group_id:
            return get_auth_group(id=auth_group_id)
    except Exception as e:
        logger.warning(f"Could not resolve auth group: {e}")
    return None


def resolve_auth_group_name(
    auth_group: Optional[str] = None, auth_group_id: Optional[str] = None
) -> Optional[str]:
    group = resolve_auth_group(auth_group=auth_group, auth_group_id=auth_group_id)
    return group.get("name") if isinstance(group, dict) else None


def flatten_record(record: Any) -> Dict[str, Any]:
    """Merge nested `school` and `user` sub-records onto the top level."""
    if not isinstance(record, dict):
        return {}
    user = record.get("user") if isinstance(record.get("user"), dict) else {}
    school = record.get("school") if isinstance(record.get("school"), dict) else {}
    flat = {**record, **{k: v for k, v in school.items() if k != "name"}, **user}
    flat["school_id"] = record.get("school_id") or school.get("id")
    flat["school_code"] = (
        record.get("school_code")
        or school.get("school_code")
        or school.get("code")
        or record.get("code")
    )
    flat["code"] = record.get("code") or school.get("code")
    flat["school_name"] = (
        record.get("school_name") or school.get("school_name") or school.get("name")
    )
    return flat


def build_token_data(
    record: Any,
    user_type: str,
    group: str,
    identifiers: Dict[str, Any],
    user_validated: bool = True,
) -> Optional[Dict[str, Any]]:
    """Build the claims stored under the token's custom data."""
    merged = {**flatten_record(record), **identifiers}
    user_id = _str_or_none(
        identifiers.get("user_id") or merged.get("user_id") or merged.get("id")
    )
    if not user_id or not group:
        return None

    display_id = _str_or_none(
        identifiers.get("display_id")
        or _first(merged, ["display_id"] + IDENTIFIER_KEYS)
        or user_id
    )
    display_id_type = identifiers.get("display_id_type") or merged.get(
        "display_id_type"
    )
    if not display_id_type:
        for key in ["student_id", "apaar_id", "teacher_id", "candidate_id"]:
            if display_id == _str_or_none(merged.get(key)):
                display_id_type = key
                break
        else:
            if display_id in {
                _str_or_none(merged.get("school_code")),
                _str_or_none(merged.get("code")),
            }:
                display_id_type = "school_code"
            else:
                display_id_type = "user_id"

    data: Dict[str, Any] = {
        "group": group,
        "user_id": user_id,
        "display_id": display_id,
        "display_id_type": display_id_type,
        "user_type": user_type,
        "user_validated": user_validated,
    }
    for key in IDENTIFIER_KEYS:
        value = _str_or_none(merged.get(key))
        if value:
            data[key] = value

    has_school = bool(merged.get("school_code") or merged.get("code"))
    data["profile"] = {
        "auth": {
            "user_id": user_id,
            "group": group,
            "user_type": user_type,
            "display_id": display_id,
            "display_id_type": display_id_type,
        },
        "user": _pick(merged, USER_FIELDS),
        "student": _pick(merged, STUDENT_FIELDS) if user_type == "student" else None,
        "teacher": _pick(merged, TEACHER_FIELDS) if user_type == "teacher" else None,
        "candidate": (
            _pick(merged, CANDIDATE_FIELDS) if user_type == "candidate" else None
        ),
        "school": (
            _pick(merged, SCHOOL_FIELDS)
            if user_type == "school" or has_school
            else None
        ),
    }
    return data


def encode(payload: Dict[str, Any]) -> str:
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def issue_session_tokens(
    subject: str,
    data: Dict[str, Any],
    session_mode: str = PERSISTENT_SESSION_MODE,
    audience: Optional[str] = None,
    with_refresh: bool = True,
) -> Dict[str, Any]:
    """Mint an access token (and a refresh token for persistent sessions)."""
    is_persistent = session_mode == PERSISTENT_SESSION_MODE
    ttl = ACCESS_TOKEN_TTL if is_persistent else LAUNCH_TOKEN_TTL
    access_payload = {
        "sub": subject,
        "exp": _now() + ttl,
        **data,
        "session_mode": session_mode,
        "persist": is_persistent,
    }
    if audience:
        access_payload["aud"] = audience

    refresh_token = ""
    if is_persistent and with_refresh:
        refresh_token = encode(
            {
                "sub": subject,
                "exp": _now() + REFRESH_TOKEN_TTL,
                "type": "refresh",
                **data,
            }
        )

    return {
        "access_token": encode(access_payload),
        "refresh_token": refresh_token,
        "session_mode": session_mode,
    }


def issue_launch_token(verified_payload: Dict[str, Any], audience: str) -> str:
    """Derive a short-lived launch token from an already verified access token."""
    data = {k: v for k, v in verified_payload.items() if k not in RESERVED_CLAIMS}
    return issue_session_tokens(
        subject=str(verified_payload.get("sub")),
        data=data,
        session_mode=LAUNCH_SESSION_MODE,
        audience=audience,
    )["access_token"]


def tokens_for_record(
    record: Any,
    user_type: str,
    identifiers: Dict[str, Any],
    group_name: Optional[str],
    user_validated: bool = True,
) -> Dict[str, Any]:
    """Session tokens for a verified record, or {} when the auth group is unknown."""
    if not group_name:
        return {}

    data = build_token_data(record, user_type, group_name, identifiers, user_validated)
    if not data:
        return {}

    tokens = issue_session_tokens(data["user_id"], data, with_refresh=user_validated)
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }


def invalid_verification_response(
    group_name: Optional[str], user_type: str, typed_id: Optional[str]
) -> Dict[str, Any]:
    """Testing auth groups still get an unvalidated token for the typed id."""
    response: Dict[str, Any] = {"is_valid": False}
    if group_name in TESTING_AUTH_GROUPS and typed_id:
        typed_id = str(typed_id)
        response.update(
            tokens_for_record(
                None,
                user_type,
                {"user_id": typed_id, "display_id": typed_id},
                group_name,
                user_validated=False,
            )
        )
    return response
