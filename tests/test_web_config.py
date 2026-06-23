from james_web_tool.config import APP_NAME, default_data_dir, default_db_path, default_logo_path, default_output_dir
from james_web_tool.models import PlanGrant, PlanTier, voice_display_options


def test_app_name_and_default_paths_are_stable(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("JAMES_WEB_LOGO_PATH", str(tmp_path / "logo.jpg"))

    assert APP_NAME == "James Audio & Srt Generator"
    assert default_data_dir() == tmp_path
    assert default_db_path() == tmp_path / "james_web_tool.sqlite3"
    assert default_output_dir() == tmp_path / "outputs"
    assert default_logo_path() == tmp_path / "logo.jpg"


def test_plan_grant_days_and_tiers():
    assert PlanGrant.ONE_MONTH.days == 30
    assert PlanGrant.THREE_MONTHS.tier == PlanTier.VIP
    assert PlanGrant.SIX_MONTHS.tier == PlanTier.VVIP
    assert PlanGrant.ONE_YEAR.days == 365
    assert PlanGrant.LIFETIME.days is None


def test_voice_display_options_include_myanmar_defaults():
    options = voice_display_options()

    assert options["James Velvet MM-02 (Female)"] == "my-MM-NilarNeural"
    assert options["James Hero MM-01 (Male)"] == "my-MM-ThihaNeural"
