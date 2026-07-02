from pathlib import Path

from james_web_tool.admin import create_paid_user
from james_web_tool.database import create_user, init_db, list_users
from james_web_tool.generator import generate_for_user
from james_web_tool.generator import generate_voice_preview, voice_preview_text
from james_web_tool.models import PlanGrant, PlanTier


def fake_tts(text: str, mp3_path: Path, voice_id: str, rate: str = "+0%") -> float:
    mp3_path.write_bytes(b"fake mp3")
    return 2.5


def fake_gemini_tts(
    text: str,
    mp3_path: Path,
    voice_id: str,
    model_id: str,
    api_key: str,
    emotion: str,
) -> float:
    mp3_path.write_bytes(b"fake gemini mp3")
    return 4.0


def fake_elevenlabs_tts(
    text: str,
    mp3_path: Path,
    voice_id: str,
    api_key: str,
    emotion: str,
) -> float:
    mp3_path.write_bytes(b"fake elevenlabs mp3")
    return 4.5


def test_generate_for_user_writes_mp3_srt_and_records_job(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    output_dir = tmp_path / "outputs"
    init_db(db_path)
    user = create_paid_user(db_path, pin="777777", grant=PlanGrant.ONE_MONTH)

    result = generate_for_user(
        db_path=db_path,
        output_dir=output_dir,
        user_id=user["user_id"],
        text="မင်္ဂလာပါ။ နေကောင်းလား။",
        voice_label="မြန်မာမ ၂",
        srt_format="2 Lines",
        file_name="test_output",
        tts_func=fake_tts,
    )

    assert result.mp3_path.exists()
    assert result.srt_path.exists()
    srt = result.srt_path.read_text(encoding="utf-8-sig")
    assert "00:00:00,000" in srt
    assert "မင်္ဂလာပါ။" in srt
    assert list_users(db_path)[0]["job_count"] == 1


def test_admin_can_generate_without_database_user(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    output_dir = tmp_path / "outputs"
    init_db(db_path)

    result = generate_for_user(
        db_path=db_path,
        output_dir=output_dir,
        user_id="ADMIN",
        text="မင်္ဂလာပါ။",
        voice_label="မြန်မာမ ၂",
        srt_format="YouTube",
        file_name="admin_output",
        pronunciation_rules="မင်္ဂလာပါ => မင်္ဂလာပါ",
        tts_func=fake_tts,
    )

    assert result.mp3_path.exists()
    assert result.srt_path.exists()


def test_generate_for_user_applies_pronunciation_rules_and_rate(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    output_dir = tmp_path / "outputs"
    init_db(db_path)
    user = create_paid_user(db_path, pin="888888", grant=PlanGrant.SIX_MONTHS)
    calls = {}

    def capture_tts(text: str, mp3_path: Path, voice_id: str, rate: str = "+0%") -> float:
        calls["text"] = text
        calls["voice_id"] = voice_id
        calls["rate"] = rate
        mp3_path.write_bytes(b"fake mp3")
        return 3.0

    result = generate_for_user(
        db_path=db_path,
        output_dir=output_dir,
        user_id=user["user_id"],
        text="Myanmar_TTSaa စမ်းသပ်မယ်။",
        voice_label="မြန်မာကျား ၁",
        srt_format="YouTube",
        file_name="unsafe:/name",
        pronunciation_rules="Myanmar_TTSaa => မြန်မာ တီတီအက်စ်အေ",
        rate=40,
        pitch=0,
        volume_boost=10,
        emotion="Movie Recap",
        engine="Free Edge TTS",
        api_key="",
        tts_func=capture_tts,
    )

    assert calls["text"] == "မြန်မာ တီတီအက်စ်အေ စမ်းသပ်မယ်။"
    assert calls["voice_id"] == "my-MM-ThihaNeural"
    assert calls["rate"] == "+40%"
    assert "unsafe/name" not in result.mp3_path.name
    assert "မြန်မာ တီတီအက်စ်အေ" in result.srt_path.read_text(encoding="utf-8-sig")


def test_free_user_is_limited_to_short_basic_generation(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    output_dir = tmp_path / "outputs"
    init_db(db_path)
    user = create_user(db_path, pin="111111", plan_tier=PlanTier.NONE, expires_at=None)

    try:
        generate_for_user(
            db_path=db_path,
            output_dir=output_dir,
            user_id=user["user_id"],
            text="က" * 5001,
            voice_label="မြန်မာမ ၂",
            srt_format="Single Line",
            file_name="free_output",
            tts_func=fake_tts,
        )
    except ValueError as exc:
        assert "Free plan limit is 5,000 characters" in str(exc)
    else:
        raise AssertionError("Expected free character limit error")


def test_vip_can_use_advanced_features_and_long_text(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    output_dir = tmp_path / "outputs"
    init_db(db_path)
    user = create_paid_user(db_path, pin="222222", grant=PlanGrant.ONE_MONTH)

    result = generate_for_user(
        db_path=db_path,
        output_dir=output_dir,
        user_id=user["user_id"],
        text=("မင်္ဂလာပါ။ " * 800).strip(),
        voice_label="မြန်မာမ ၂",
        srt_format="YouTube",
        file_name="vip_output",
        pronunciation_rules="မင်္ဂလာပါ => မင်္ဂလာပါ",
        tts_func=fake_tts,
    )

    assert result.mp3_path.exists()


def test_six_month_plan_is_vip_and_can_use_pronunciation_rules_and_youtube_format(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    output_dir = tmp_path / "outputs"
    init_db(db_path)
    user = create_paid_user(db_path, pin="333333", grant=PlanGrant.SIX_MONTHS)
    assert user["plan_tier"] == PlanTier.VIP.value

    result = generate_for_user(
        db_path=db_path,
        output_dir=output_dir,
        user_id=user["user_id"],
        text="James စမ်းမယ်။",
        voice_label="မြန်မာမ ၂",
        srt_format="YouTube",
        file_name="vip_output",
        pronunciation_rules="James => ဂျိမ်းစ်",
        tts_func=fake_tts,
    )

    assert result.srt_path.exists()
    assert "ဂျိမ်းစ်" in result.srt_path.read_text(encoding="utf-8-sig")


def test_gemini_engine_routes_to_gemini_voice_model_and_api_key(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    output_dir = tmp_path / "outputs"
    init_db(db_path)
    user = create_paid_user(db_path, pin="444444", grant=PlanGrant.SIX_MONTHS)
    calls = {}

    def capture_gemini_tts(
        text: str,
        mp3_path: Path,
        voice_id: str,
        model_id: str,
        api_key: str,
        emotion: str,
    ) -> float:
        calls["text"] = text
        calls["voice_id"] = voice_id
        calls["model_id"] = model_id
        calls["api_key"] = api_key
        calls["emotion"] = emotion
        mp3_path.write_bytes(b"fake gemini mp3")
        return 4.0

    result = generate_for_user(
        db_path=db_path,
        output_dir=output_dir,
        user_id=user["user_id"],
        text="မင်္ဂလာပါ။",
        voice_label="ကြယ်နု ၁",
        srt_format="Single Line",
        file_name="gemini_output",
        emotion="Excited (စိတ်လှုပ်ရှား)",
        engine="Gemini API (Key Required)",
        api_key="secret-key",
        gemini_model="Gemini 3.1 Flash",
        tts_func=fake_tts,
        gemini_tts_func=capture_gemini_tts,
    )

    assert result.mp3_path.exists()
    assert calls["voice_id"] == "Aoede"
    assert calls["model_id"] == "gemini-3.1-flash-tts-preview"
    assert calls["api_key"] == "secret-key"
    assert calls["emotion"] == "Excited (စိတ်လှုပ်ရှား)"


def test_elevenlabs_engine_routes_to_elevenlabs_voice_and_api_key(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    output_dir = tmp_path / "outputs"
    init_db(db_path)
    user = create_paid_user(db_path, pin="555555", grant=PlanGrant.ONE_MONTH)
    calls = {}

    def capture_elevenlabs_tts(
        text: str,
        mp3_path: Path,
        voice_id: str,
        api_key: str,
        emotion: str,
    ) -> float:
        calls["text"] = text
        calls["voice_id"] = voice_id
        calls["api_key"] = api_key
        calls["emotion"] = emotion
        mp3_path.write_bytes(b"fake elevenlabs mp3")
        return 4.5

    result = generate_for_user(
        db_path=db_path,
        output_dir=output_dir,
        user_id=user["user_id"],
        text="မင်္ဂလာပါ။",
        voice_label="အေးချမ်းမ ၁",
        srt_format="Single Line",
        file_name="elevenlabs_output",
        emotion="Storytelling (ပုံပြင်ပြော)",
        engine="ElevenLabs API (Key Required)",
        api_key="eleven-key",
        tts_func=fake_tts,
        gemini_tts_func=fake_gemini_tts,
        elevenlabs_tts_func=capture_elevenlabs_tts,
    )

    assert result.mp3_path.exists()
    assert calls["voice_id"] == "21m00Tcm4TlvDq8ikWAM"
    assert calls["api_key"] == "eleven-key"
    assert calls["emotion"] == "Storytelling (ပုံပြင်ပြော)"


def test_generate_voice_preview_uses_edge_voice_and_rate(tmp_path):
    calls = {}

    def capture_tts(text: str, mp3_path: Path, voice_id: str, rate: str = "+0%") -> float:
        calls["text"] = text
        calls["voice_id"] = voice_id
        calls["rate"] = rate
        mp3_path.write_bytes(b"fake edge preview")
        return 1.0

    preview_path = generate_voice_preview(
        output_dir=tmp_path,
        engine="Free Edge TTS",
        voice_label="မြန်မာကျား ၁",
        rate=40,
        pitch=0,
        volume_boost=10,
        emotion="Movie Recap (ဇာတ်လမ်းပြော)",
        api_key="",
        gemini_model="Gemini 3.1 Flash",
        tts_func=capture_tts,
        gemini_tts_func=fake_gemini_tts,
    )

    assert preview_path.exists()
    assert calls["voice_id"] == "my-MM-ThihaNeural"
    assert calls["rate"] == "+40%"
    assert "မင်္ဂလာပါ" in calls["text"]


def test_voice_preview_text_mentions_selected_edge_voice_name():
    text = voice_preview_text("မြန်မာကျား ၁")

    assert text == "မင်္ဂလာပါ။ ကျွန်တော်ကတော့ မြန်မာကျား ၁ပါ။ စာကနေအသံပြောင်းပေးမှာဖြစ်ပါတယ်။"


def test_voice_preview_text_strips_voice_description():
    text = voice_preview_text("မြန်မာကျား ၁")

    assert "မြန်မာကျား ၁ပါ" in text
    assert "Male" not in text
    assert "Female" not in text


def test_generate_voice_preview_uses_gemini_voice_model_and_key(tmp_path):
    calls = {}

    def capture_gemini_tts(
        text: str,
        mp3_path: Path,
        voice_id: str,
        model_id: str,
        api_key: str,
        emotion: str,
    ) -> float:
        calls["text"] = text
        calls["voice_id"] = voice_id
        calls["model_id"] = model_id
        calls["api_key"] = api_key
        calls["emotion"] = emotion
        mp3_path.write_bytes(b"fake gemini preview")
        return 1.0

    preview_path = generate_voice_preview(
        output_dir=tmp_path,
        engine="Gemini API (Key Required)",
        voice_label="ကြယ်နု ၁",
        rate=40,
        pitch=0,
        volume_boost=10,
        emotion="Excited (စိတ်လှုပ်ရှား)",
        api_key="secret-key",
        gemini_model="Gemini 3.1 Flash",
        tts_func=fake_tts,
        gemini_tts_func=capture_gemini_tts,
    )

    assert preview_path.exists()
    assert calls["voice_id"] == "Aoede"
    assert calls["model_id"] == "gemini-3.1-flash-tts-preview"
    assert calls["api_key"] == "secret-key"
    assert calls["emotion"] == "Excited (စိတ်လှုပ်ရှား)"
    assert "ကြယ်နု ၁ပါ" in calls["text"]


def test_generate_voice_preview_requires_gemini_api_key(tmp_path):
    try:
        generate_voice_preview(
            output_dir=tmp_path,
            engine="Gemini API (Key Required)",
            voice_label="ကြယ်နု ၁",
            rate=40,
            pitch=0,
            volume_boost=10,
            emotion="Movie Recap (ဇာတ်လမ်းပြော)",
            api_key="",
            gemini_model="Gemini 3.1 Flash",
            tts_func=fake_tts,
            gemini_tts_func=fake_gemini_tts,
        )
    except ValueError as exc:
        assert "Gemini API Key required" in str(exc)
    else:
        raise AssertionError("Expected missing Gemini API key error")


def test_generate_voice_preview_uses_elevenlabs_voice_and_key(tmp_path):
    calls = {}

    def capture_elevenlabs_tts(
        text: str,
        mp3_path: Path,
        voice_id: str,
        api_key: str,
        emotion: str,
    ) -> float:
        calls["text"] = text
        calls["voice_id"] = voice_id
        calls["api_key"] = api_key
        calls["emotion"] = emotion
        mp3_path.write_bytes(b"fake elevenlabs preview")
        return 1.0

    preview_path = generate_voice_preview(
        output_dir=tmp_path,
        engine="ElevenLabs API (Key Required)",
        voice_label="အေးချမ်းမ ၁",
        rate=40,
        pitch=0,
        volume_boost=10,
        emotion="Movie Recap (ဇာတ်လမ်းပြော)",
        api_key="eleven-key",
        gemini_model="Gemini 3.1 Flash",
        tts_func=fake_tts,
        gemini_tts_func=fake_gemini_tts,
        elevenlabs_tts_func=capture_elevenlabs_tts,
    )

    assert preview_path.exists()
    assert calls["voice_id"] == "21m00Tcm4TlvDq8ikWAM"
    assert calls["api_key"] == "eleven-key"
    assert "အေးချမ်းမ ၁ပါ" in calls["text"]


def test_generate_voice_preview_requires_elevenlabs_api_key(tmp_path):
    try:
        generate_voice_preview(
            output_dir=tmp_path,
            engine="ElevenLabs API (Key Required)",
            voice_label="အေးချမ်းမ ၁",
            rate=40,
            pitch=0,
            volume_boost=10,
            emotion="Movie Recap (ဇာတ်လမ်းပြော)",
            api_key="",
            gemini_model="Gemini 3.1 Flash",
            tts_func=fake_tts,
            gemini_tts_func=fake_gemini_tts,
            elevenlabs_tts_func=fake_elevenlabs_tts,
        )
    except ValueError as exc:
        assert "ElevenLabs API Key required" in str(exc)
    else:
        raise AssertionError("Expected missing ElevenLabs API key error")




