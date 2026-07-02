from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from james_web_tool.ui import build_app
from james_web_tool import ui


def test_build_app_returns_gradio_blocks(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))

    app = build_app()

    assert app is not None
    assert app.__class__.__name__ == "Blocks"


def test_generator_contains_premium_tts_controls(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))

    app = build_app()
    labels = {getattr(component, "label", None) for component in app.blocks.values()}

    assert "TTS Engine" in labels
    assert "API Key (Gemini / ElevenLabs)" in labels
    assert "Gemini Model" in labels
    assert "Pronunciation Rules (အသံထွက်ပြင်ဆင်ရန်)" in labels
    assert "သိမ်းမယ့်ဖိုင် နာမည် (File Name)" in labels
    assert "[VIP] Voice" in labels
    assert "ခံစားမှု / အသံပုံစံ (Emotion)" in labels
    assert "SRT Format Type" in labels
    assert "Base Tone (Pitch)" in labels
    assert "Base Speed (Rate)" in labels
    assert "Volume Booster (+dB)" in labels


def test_generator_default_file_name_is_james_ttsrt(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))

    app = build_app()
    file_name_components = [
        component
        for component in app.blocks.values()
        if getattr(component, "label", None) == "သိမ်းမယ့်ဖိုင် နာမည် (File Name)"
    ]

    assert file_name_components
    assert getattr(file_name_components[0], "value", None) == "James_TTSrt"


def test_generator_has_voice_preview_audio(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))

    app = build_app()
    labels = {getattr(component, "label", None) for component in app.blocks.values()}

    assert "Voice Preview" in labels


def test_free_marketing_tool_controls_are_present(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))

    app = build_app()
    labels = {getattr(component, "label", None) for component in app.blocks.values()}

    assert "Free Myanmar Text" in labels
    assert "Free Voice" in labels
    assert "Free SRT Format" in labels
    assert "Free MP3 Download" in labels
    assert "Free SRT Download" in labels
    markdown_values = "\n".join(
        str(getattr(component, "value", ""))
        for component in app.blocks.values()
        if component.__class__.__name__ == "Markdown"
    )
    assert "Free vs VIP vs Lifetime" in markdown_values
    assert "5000 characters" in markdown_values
    assert "3 times / day" in markdown_values
    assert "unlimited characters" in markdown_values


def test_admin_panel_is_not_a_public_top_level_tab(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))

    app = build_app()
    visible_tabs = {
        getattr(component, "label", None)
        for component in app.blocks.values()
        if component.__class__.__name__ == "Tab" and getattr(component, "visible", True)
    }
    labels = {getattr(component, "label", None) for component in app.blocks.values()}
    button_values = [getattr(component, "value", None) for component in app.blocks.values()]

    assert "Admin" not in visible_tabs
    assert "Free Tool" in visible_tabs
    assert "Login" in visible_tabs
    assert "Generator" not in visible_tabs
    assert "Admin Panel" in labels
    assert "Delete User" in button_values
    assert "Remember admin on this browser" in labels
    assert "Forget saved admin login" in button_values
    assert "Grant 6M VIP" in button_values
    assert "Grant 1Y VIP" in button_values
    assert "Grant 6M VIP" in button_values
    assert "Grant 1Y VIP" in button_values


def test_browser_state_falls_back_to_session_state(monkeypatch):
    monkeypatch.delattr(ui.gr, "BrowserState", raising=False)

    state = ui.browser_state_or_session_state({})

    assert state.__class__.__name__ == "State"


def test_free_usage_allows_three_jobs_per_day_then_blocks():
    usage = {}

    usage = ui.updated_free_usage_or_error(usage, today="2026-06-23")
    usage = ui.updated_free_usage_or_error(usage, today="2026-06-23")
    usage = ui.updated_free_usage_or_error(usage, today="2026-06-23")

    try:
        ui.updated_free_usage_or_error(usage, today="2026-06-23")
    except ValueError as exc:
        assert "Free tool limit is 3 times / day" in str(exc)
    else:
        raise AssertionError("Expected free daily limit error")


def test_free_usage_resets_on_new_day():
    usage = {"date": "2026-06-22", "count": 3}

    updated = ui.updated_free_usage_or_error(usage, today="2026-06-23")

    assert updated == {"date": "2026-06-23", "count": 1}


def test_remaining_days_text_shows_days_hours_and_lifetime():
    now = datetime(2026, 6, 23, 10, 0, tzinfo=timezone.utc)
    expires = (now + timedelta(days=29, hours=3)).isoformat()

    assert ui.remaining_days_text("VIP", expires, now=now) == "ကျန်ရက်: 29 days 3 hours"
    assert ui.remaining_days_text("LIFETIME", None, now=now) == "ကျန်ရက်: Lifetime"
    assert ui.remaining_days_text("VIP", (now - timedelta(minutes=1)).isoformat(), now=now) == "ကျန်ရက်: Expired"


def test_user_status_text_includes_remaining_days():
    now = datetime(2026, 6, 23, 10, 0, tzinfo=timezone.utc)
    expires = (now + timedelta(days=30)).isoformat()

    text = ui.user_status_text("J-TEST", "VIP", expires, now=now)

    assert text == "Logged in: J-TEST • VIP • ကျန်ရက်: 30 days"


def test_login_handler_display_includes_remaining_days(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    from james_web_tool.database import create_user, init_db
    from james_web_tool.models import PlanTier

    db_path = tmp_path / "james_web_tool.sqlite3"
    init_db(db_path)
    create_user(db_path, pin="246810", plan_tier=PlanTier.VIP, expires_at=expires)

    app = build_app()
    login_dependency = next(
        dep
        for dep in app.fns.values()
        if getattr(dep.fn, "__name__", "") == "do_login"
    )

    outputs = login_dependency.fn("246810", False)

    assert "VIP" in outputs[3]
    assert "ကျန်ရက်:" in outputs[3]
    assert outputs[8]["visible"] is False
    assert outputs[9]["visible"] is True


def test_admin_can_use_generator_without_user_pin(tmp_path, monkeypatch):
    monkeypatch.setenv("JAMES_WEB_DATA_DIR", str(tmp_path))
    calls = {}

    def fake_generate_for_user(db_path, output_dir, user_id, text, voice_label, srt_format, file_name, **kwargs):
        calls["user_id"] = user_id
        calls["text"] = text
        mp3_path = tmp_path / "admin.mp3"
        srt_path = tmp_path / "admin.srt"
        mp3_path.write_bytes(b"mp3")
        srt_path.write_text("srt", encoding="utf-8")
        return SimpleNamespace(mp3_path=mp3_path, srt_path=srt_path, message="ok")

    monkeypatch.setattr(ui, "generate_for_user", fake_generate_for_user)
    app = build_app()
    generate_dependency = next(
        dep
        for dep in app.fns.values()
        if getattr(dep.fn, "__name__", "") == "do_generate"
    )

    outputs = generate_dependency.fn(
        "ADMIN",
        "မင်္ဂလာပါ။",
        "Free Edge TTS",
        "",
        "Gemini 3.1 Flash",
        "",
        "admin_output",
        "မြန်မာကျား ၁",
        "Movie Recap",
        "Single Line",
        0,
        40,
        10,
    )

    assert calls["user_id"] == "ADMIN"
    assert outputs[0] == "ok"
