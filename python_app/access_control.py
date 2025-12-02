from __future__ import annotations

from typing import Literal

from .config import config
from .logger import log_debug

Role = Literal["admin", "allowed", "blocked", "default"]


def get_user_role(user_id: str) -> Role:
    if user_id in config.access.admins:
        return "admin"
    if user_id in config.access.blocklist:
        return "blocked"
    if user_id in config.access.allowlist:
        return "allowed"
    return "default"


def can_use_feature(user_id: str, feature: Literal["agent", "openai"]) -> bool:
    role = get_user_role(user_id)
    log_debug("Evaluating access", {"user": user_id, "role": role, "feature": feature})

    if role == "blocked":
        return False
    if role == "admin":
        return True
    if role == "allowed":
        return True
    # default role: honor default_allow flag
    return config.access.default_allow
