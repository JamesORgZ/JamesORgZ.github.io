from datetime import datetime, timedelta, timezone

from james_web_tool.auth import login_with_pin, user_has_access
from james_web_tool.config import DEFAULT_ADMIN_PIN
from james_web_tool.database import create_user, init_db
from james_web_tool.models import PlanTier


def test_admin_pin_logs_in_as_admin(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)

    result = login_with_pin(db_path, DEFAULT_ADMIN_PIN)

    assert result.ok is True
    assert result.is_admin is True


def test_active_user_can_login(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    expires = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    create_user(db_path, pin="111111", plan_tier=PlanTier.VIP, expires_at=expires)

    result = login_with_pin(db_path, "111111")

    assert result.ok is True
    assert result.is_admin is False
    assert result.plan_tier == PlanTier.VIP


def test_expired_user_is_blocked(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    expired = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    user = create_user(db_path, pin="333333", plan_tier=PlanTier.VIP, expires_at=expired)

    assert user_has_access(user) is False
    assert login_with_pin(db_path, "333333").ok is False


def test_login_syncs_remote_paid_pin_when_not_in_local_database(tmp_path, monkeypatch):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    def fake_remote_lookup(pin: str):
        assert pin == "999888"
        return {
            "user_id": "J-REMOTE",
            "pin": "999888",
            "plan_tier": PlanTier.VIP.value,
            "expires_at": expires,
            "status": "active",
        }

    monkeypatch.setattr("james_web_tool.auth.lookup_remote_user_by_pin", fake_remote_lookup)

    result = login_with_pin(db_path, "999888")

    assert result.ok is True
    assert result.user_id == "J-REMOTE"
    assert result.plan_tier == PlanTier.VIP
