from datetime import datetime, timezone

from james_web_tool.database import (
    create_user,
    get_user_by_pin,
    init_db,
    list_users,
    record_job,
    search_users,
)
from james_web_tool.models import PlanTier


def test_create_and_find_user_by_pin(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)

    user = create_user(db_path, pin="123456", plan_tier=PlanTier.VIP, expires_at="2099-01-01T00:00:00+00:00")
    found = get_user_by_pin(db_path, "123456")

    assert found is not None
    assert found["user_id"] == user["user_id"]
    assert found["plan_tier"] == "VIP"
    assert found["status"] == "active"


def test_search_users_matches_user_id_and_pin(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    user = create_user(db_path, pin="654321", plan_tier=PlanTier.VVIP, expires_at="2099-01-01T00:00:00+00:00")

    assert search_users(db_path, user["user_id"])[0]["pin"] == "654321"
    assert search_users(db_path, "654")[0]["user_id"] == user["user_id"]


def test_record_job_and_list_users(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    user = create_user(db_path, pin="222222", plan_tier=PlanTier.VIP, expires_at=None)

    record_job(
        db_path,
        user_id=user["user_id"],
        input_chars=42,
        voice_label="မြန်မာမ ၂",
        mp3_path="outputs/test.mp3",
        srt_path="outputs/test.srt",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    rows = list_users(db_path)
    assert rows[0]["user_id"] == user["user_id"]
    assert rows[0]["job_count"] == 1


