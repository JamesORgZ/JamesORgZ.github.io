from datetime import datetime, timedelta, timezone

import pandas as pd

from james_web_tool.admin import create_paid_user, delete_user, disable_user, grant_plan, revoke_user
from james_web_tool.auth import login_with_pin
from james_web_tool.database import connect, create_user, get_user_by_id, init_db, list_users, record_job
from james_web_tool.models import PlanGrant, PlanTier
from james_web_tool.ui import selected_user_id_from_table
from james_web_tool.ui import target_user_id_from_target_or_search
from james_web_tool.ui import remember_admin_payload, should_restore_admin


def test_create_paid_user_sets_plan_and_pin(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)

    user = create_paid_user(db_path, pin="444444", grant=PlanGrant.ONE_MONTH)

    assert user["pin"] == "444444"
    assert user["plan_tier"] == "VIP"
    assert user["expires_at"] is not None


def test_grant_lifetime_sets_no_expiry(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    user = create_paid_user(db_path, pin="555555", grant=PlanGrant.ONE_MONTH)

    updated = grant_plan(db_path, user["user_id"], PlanGrant.LIFETIME)

    assert updated["plan_tier"] == PlanTier.LIFETIME.value
    assert updated["expires_at"] is None


def test_revoke_and_disable_user(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    user = create_paid_user(db_path, pin="666666", grant=PlanGrant.THREE_MONTHS)

    revoked = revoke_user(db_path, user["user_id"])
    assert revoked["plan_tier"] == PlanTier.NONE.value

    disabled = disable_user(db_path, user["user_id"])
    assert disabled["status"] == "disabled"
    assert get_user_by_id(db_path, user["user_id"])["status"] == "disabled"


def test_delete_user_removes_user_and_jobs(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    user = create_paid_user(db_path, pin="777000", grant=PlanGrant.ONE_MONTH)
    record_job(
        db_path,
        user_id=user["user_id"],
        input_chars=10,
        voice_label="James Velvet MM-02 (Female)",
        mp3_path="out.mp3",
        srt_path="out.srt",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    deleted = delete_user(db_path, user["user_id"])

    with connect(db_path) as conn:
        job_count = conn.execute("SELECT COUNT(*) FROM jobs WHERE user_id = ?", (user["user_id"],)).fetchone()[0]
    assert deleted["user_id"] == user["user_id"]
    assert get_user_by_id(db_path, user["user_id"]) is None
    assert job_count == 0


def test_admin_actions_raise_clear_error_for_missing_target(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)

    for action in (
        lambda: grant_plan(db_path, "", PlanGrant.ONE_MONTH),
        lambda: revoke_user(db_path, ""),
        lambda: disable_user(db_path, ""),
        lambda: delete_user(db_path, ""),
    ):
        try:
            action()
        except ValueError as exc:
            assert "Target User ID required" in str(exc)
        else:
            raise AssertionError("Expected target user validation error")


def test_expired_user_auto_updates_status_on_login_and_list(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    expired_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    user = create_user(db_path, pin="121212", plan_tier=PlanTier.VIP, expires_at=expired_at)

    login = login_with_pin(db_path, "121212")
    rows = list_users(db_path)

    assert not login.ok
    assert login.message == "Expired"
    assert get_user_by_id(db_path, user["user_id"])["status"] == "expired"
    assert rows[0]["status"] == "expired"


def test_table_selection_fills_target_user_id():
    table = [["J-ABC123", "111111", "VIP", "2026-07-22", "active", "0"]]

    assert selected_user_id_from_table(table, (0, 0)) == "J-ABC123"
    assert selected_user_id_from_table(table, (0, 3)) == "J-ABC123"


def test_table_selection_supports_dataframe_values():
    dataframe = pd.DataFrame(
        [["J-BAAE2D", "112884", "VIP", "2026-07-22", "active", "0"]],
        columns=["User ID", "PIN", "Plan", "Expires", "Status", "Jobs"],
    )
    dict_value = {
        "data": [["J-707058", "12221", "VIP", "2026-07-22", "active", "0"]],
        "headers": ["User ID", "PIN", "Plan", "Expires", "Status", "Jobs"],
    }

    assert selected_user_id_from_table(dataframe, (0, 1)) == "J-BAAE2D"
    assert selected_user_id_from_table(dict_value, (0, 1)) == "J-707058"


def test_admin_action_can_resolve_target_from_search_pin(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    user = create_paid_user(db_path, pin="112884", grant=PlanGrant.ONE_MONTH)

    assert target_user_id_from_target_or_search(db_path, "", "112884") == user["user_id"]
    assert target_user_id_from_target_or_search(db_path, user["user_id"], "112884") == user["user_id"]


def test_admin_remember_state_only_saves_for_admin_when_checked():
    assert remember_admin_payload(is_admin=True, remember=True) == {"admin_remembered": True}
    assert remember_admin_payload(is_admin=True, remember=False) == {}
    assert remember_admin_payload(is_admin=False, remember=True) == {}
    assert should_restore_admin({"admin_remembered": True})
    assert not should_restore_admin({})
