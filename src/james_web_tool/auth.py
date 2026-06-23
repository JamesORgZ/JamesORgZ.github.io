from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DEFAULT_ADMIN_PIN
from .database import expire_due_users, get_user_by_pin, update_user, upsert_remote_user
from .models import LoginResult, PlanTier


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def user_has_access(user: dict[str, Any]) -> bool:
    if user.get("status") != "active":
        return False
    if user.get("plan_tier") == PlanTier.LIFETIME.value and user.get("expires_at") is None:
        return True
    expires = parse_datetime(user.get("expires_at"))
    if expires is None:
        return user.get("plan_tier") == PlanTier.LIFETIME.value
    return expires > datetime.now(timezone.utc)


def lookup_remote_user_by_pin(pin: str) -> dict[str, Any] | None:
    url = os.getenv("JAMES_REMOTE_AUTH_URL", "").strip()
    secret = os.getenv("JAMES_REMOTE_AUTH_SECRET", "").strip()
    if not url or not secret:
        return None
    payload = urllib.parse.urlencode({"pin": pin, "secret": secret}).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    if not data.get("ok") or not isinstance(data.get("user"), dict):
        return None
    return data["user"]


def sync_remote_user(db_path: Path, remote_user: dict[str, Any]) -> dict[str, Any] | None:
    try:
        return upsert_remote_user(
            db_path,
            user_id=str(remote_user["user_id"]),
            pin=str(remote_user["pin"]),
            plan_tier=PlanTier(remote_user["plan_tier"]),
            expires_at=remote_user.get("expires_at"),
            status=str(remote_user.get("status", "active")),
        )
    except Exception:
        return None


def login_with_pin(db_path: Path, pin: str) -> LoginResult:
    clean_pin = pin.strip()
    if clean_pin == DEFAULT_ADMIN_PIN:
        return LoginResult(True, True, "ADMIN", "Admin login ok", PlanTier.LIFETIME)
    expire_due_users(db_path)
    user = get_user_by_pin(db_path, clean_pin)
    if user is None:
        remote_user = lookup_remote_user_by_pin(clean_pin)
        user = sync_remote_user(db_path, remote_user) if remote_user else None
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
