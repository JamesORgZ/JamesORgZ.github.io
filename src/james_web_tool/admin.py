from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from .database import create_user, delete_user_by_id, get_user_by_id, get_user_by_telegram_id, update_user
from .models import PlanGrant, PlanTier


def expiry_for_grant(grant: PlanGrant) -> str | None:
    if grant.days is None:
        return None
    return (datetime.now(timezone.utc) + timedelta(days=grant.days)).isoformat()


def create_paid_user(db_path: Path, pin: str, grant: PlanGrant, telegram_user_id: int | str | None = None) -> dict:
    if not pin.strip():
        raise ValueError("New User PIN required.")
    if telegram_user_id is not None:
        existing = get_user_by_telegram_id(db_path, telegram_user_id)
        if existing is not None:
            return grant_plan(db_path, existing["user_id"], grant)
    return create_user(
        db_path,
        pin=pin,
        plan_tier=grant.tier,
        expires_at=expiry_for_grant(grant),
        telegram_user_id=str(telegram_user_id) if telegram_user_id is not None else None,
    )


def require_target_user(db_path: Path, user_id: str) -> dict:
    clean_user_id = user_id.strip()
    if not clean_user_id:
        raise ValueError("Target User ID required.")
    user = get_user_by_id(db_path, clean_user_id)
    if user is None:
        raise ValueError(f"User not found: {clean_user_id}")
    return user


def grant_plan(db_path: Path, user_id: str, grant: PlanGrant) -> dict:
    user = require_target_user(db_path, user_id)
    update_user(
        db_path,
        user["user_id"],
        plan_tier=grant.tier.value,
        expires_at=expiry_for_grant(grant),
        status="active",
    )
    user = get_user_by_id(db_path, user["user_id"])
    assert user is not None
    return user


def revoke_user(db_path: Path, user_id: str) -> dict:
    user = require_target_user(db_path, user_id)
    update_user(db_path, user["user_id"], plan_tier=PlanTier.NONE.value, expires_at=None, status="active")
    user = get_user_by_id(db_path, user["user_id"])
    assert user is not None
    return user


def disable_user(db_path: Path, user_id: str) -> dict:
    user = require_target_user(db_path, user_id)
    update_user(db_path, user["user_id"], status="disabled")
    user = get_user_by_id(db_path, user["user_id"])
    assert user is not None
    return user


def delete_user(db_path: Path, user_id: str) -> dict:
    user = require_target_user(db_path, user_id)
    delete_user_by_id(db_path, user["user_id"])
    return user
