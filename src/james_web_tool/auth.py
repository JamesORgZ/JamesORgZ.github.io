from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DEFAULT_ADMIN_PIN
from .database import expire_due_users, get_user_by_pin, update_user
from .models import LoginResult, PlanTier


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def user_has_access(user: dict[str, Any]) -> bool:
    if user.get("status") != "active":
        return False
    if user.get("plan_tier") in {PlanTier.LIFETIME.value, PlanTier.VVIP.value} and user.get("expires_at") is None:
        return True
    expires = parse_datetime(user.get("expires_at"))
    if expires is None:
        return user.get("plan_tier") == PlanTier.LIFETIME.value
    return expires > datetime.now(timezone.utc)


def login_with_pin(db_path: Path, pin: str) -> LoginResult:
    clean_pin = pin.strip()
    if clean_pin == DEFAULT_ADMIN_PIN:
        return LoginResult(True, True, "ADMIN", "Admin login ok", PlanTier.LIFETIME)
    expire_due_users(db_path)
    user = get_user_by_pin(db_path, clean_pin)
    if user is None:
        return LoginResult(False, False, "", "Wrong PIN")
    expires = parse_datetime(user.get("expires_at"))
    if user.get("status") == "active" and expires is not None and expires <= datetime.now(timezone.utc):
        update_user(db_path, user["user_id"], status="expired")
        return LoginResult(False, False, user["user_id"], "Expired")
    if not user_has_access(user):
        if user.get("status") == "expired":
            return LoginResult(False, False, user["user_id"], "Expired")
        return LoginResult(False, False, user["user_id"], "Disabled")
    return LoginResult(
        True,
        False,
        user["user_id"],
        "Login ok",
        PlanTier(user["plan_tier"]),
    )
