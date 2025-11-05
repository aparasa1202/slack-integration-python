from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Mapping, Optional

import jwt

from ..config import config
from ..logger import log_error, log_info


def _parse_duration(value: str | None) -> Optional[int]:
    if not value:
        return None
    if value.isdigit():
        return int(value)
    match = re.match(r"^(\d+)([smhd])$", value.strip(), flags=re.IGNORECASE)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).lower()
    multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
    return amount * multiplier


def validate_jwt(token: str | None) -> Optional[Dict[str, Any]]:
    try:
        if not token:
            log_error("JWT validation failed: No token provided")
            return None

        clean_token = re.sub(r"^Bearer\s+", "", token, flags=re.IGNORECASE)

        if not config.security.jwt_secret:
            log_error("JWT validation failed: No JWT secret configured")
            return None

        decoded = jwt.decode(
            clean_token,
            config.security.jwt_secret,
            algorithms=["HS256"],
        )
        log_info(
            "JWT validation successful",
            {"userId": decoded.get("userId"), "exp": decoded.get("exp")},
        )
        return decoded
    except jwt.ExpiredSignatureError as error:
        log_error("JWT validation failed: Token expired", error)
    except jwt.InvalidTokenError as error:
        log_error("JWT validation failed: Invalid token", error)
    except Exception as error:  # pylint: disable=broad-except
        log_error("JWT validation failed: Unknown error", error)
    return None


def generate_jwt(
    payload: Mapping[str, Any],
    expires_in: Optional[str] = None,
) -> str:
    if not config.security.jwt_secret:
        raise ValueError("JWT secret not configured")

    payload_dict = dict(payload)
    duration = _parse_duration(expires_in or config.security.jwt_expiration)
    if duration:
        payload_dict["exp"] = datetime.now(timezone.utc) + timedelta(seconds=duration)

    token = jwt.encode(payload_dict, config.security.jwt_secret, algorithm="HS256")
    log_info(
        "JWT generated successfully",
        {"userId": payload_dict.get("userId"), "expiresIn": duration},
    )
    return token


def extract_token_from_headers(headers: Mapping[str, Any]) -> Optional[str]:
    authorization = headers.get("authorization") or headers.get("Authorization")
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        return authorization[7:]
    return authorization


def jwt_middleware(
    request: Any,
    respond: Callable[[int, Dict[str, Any]], Any],
    next_func: Callable[[], Any],
) -> Any:
    try:
        token = extract_token_from_headers(getattr(request, "headers", {}))
        if not token:
            return respond(401, {"error": "No token provided"})

        decoded = validate_jwt(token)
        if not decoded:
            return respond(401, {"error": "Invalid token"})

        setattr(request, "user", decoded)
        return next_func()
    except Exception as error:  # pylint: disable=broad-except
        log_error("JWT middleware error", error)
        return respond(500, {"error": "Internal server error"})
