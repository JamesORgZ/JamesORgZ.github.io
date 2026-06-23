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
