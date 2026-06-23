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
    assert "Gemini API Key" in labels
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
    assert "Admin Panel" in labels
    assert "Delete User" in button_values
    assert "Remember admin on this browser" in labels
    assert "Forget saved admin login" in button_values


def test_browser_state_falls_back_to_session_state(monkeypatch):
    monkeypatch.delattr(ui.gr, "BrowserState", raising=False)

    state = ui.browser_state_or_session_state({})

    assert state.__class__.__name__ == "State"
