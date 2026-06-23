from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from james_srt_studio.subtitle_formatter import build_srt
from james_srt_studio.text_aligner import align_text_to_duration

from .database import get_user_by_id, record_job
from .models import GenerationResult, PlanTier
from .tts import (
    edge_voice_id_for_label,
    gemini_model_id_for_label,
    gemini_voice_id_for_label,
    generate_gemini_mp3,
    generate_mp3,
)

TtsFunc = Callable[[str, Path, str, str], float]
GeminiTtsFunc = Callable[[str, Path, str, str, str, str], float]


def safe_file_stem(file_name: str) -> str:
    allowed = "".join(ch for ch in file_name.strip() if ch.isalnum() or ch in (" ", "-", "_"))
    return allowed.strip() or "james_output"


def voice_preview_name(voice_label: str) -> str:
    clean = voice_label.split("(", 1)[0].strip()
    return clean or "James"


def voice_preview_text(voice_label: str) -> str:
    name = voice_preview_name(voice_label)
    return f"မင်္ဂလာပါ။ ကျွန်တော်ကတော့ {name}ပါ။ စာကနေအသံပြောင်းပေးမှာဖြစ်ပါတယ်။"


def apply_pronunciation_rules(text: str, rules: str) -> str:
    fixed = text
    for raw_line in rules.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for separator in ("=>", "=", "|"):
            if separator in line:
                source, replacement = line.split(separator, 1)
                source = source.strip()
                replacement = replacement.strip()
                if source:
                    fixed = fixed.replace(source, replacement)
                break
    return fixed


def edge_rate(rate: int | float | str) -> str:
    try:
        value = int(float(rate))
    except (TypeError, ValueError):
        value = 0
    value = max(-50, min(100, value))
    sign = "+" if value >= 0 else ""
    return f"{sign}{value}%"


def max_chars_for_format(srt_format: str) -> int:
    if srt_format == "2 Lines":
        return 42
    if srt_format == "YouTube":
        return 32
    return 25


def user_plan_tier(user: dict) -> PlanTier:
    try:
        return PlanTier(user.get("plan_tier", PlanTier.NONE.value))
    except ValueError:
        return PlanTier.NONE


def enforce_plan_limits(plan_tier: PlanTier, text: str, srt_format: str, pronunciation_rules: str) -> None:
    if plan_tier == PlanTier.NONE:
        if len(text) > 5000:
            raise ValueError("Free plan limit is 5,000 characters. Please upgrade to VIP.")
        if pronunciation_rules.strip() or srt_format == "YouTube":
            raise ValueError("This is a VIP feature. Please upgrade.")
        return


def generate_for_user(
    db_path: Path,
    output_dir: Path,
    user_id: str,
    text: str,
    voice_label: str,
    srt_format: str,
    file_name: str,
    pronunciation_rules: str = "",
    rate: int | float = 0,
    pitch: int | float = 0,
    volume_boost: int | float = 0,
    emotion: str = "Movie Recap",
    engine: str = "Free Edge TTS",
    api_key: str = "",
    gemini_model: str = "Gemini 3.1 Flash",
    tts_func: TtsFunc = generate_mp3,
    gemini_tts_func: GeminiTtsFunc = generate_gemini_mp3,
) -> GenerationResult:
    clean_text = apply_pronunciation_rules(text.strip(), pronunciation_rules)
    if not clean_text:
        raise ValueError("Text is empty.")
    user = get_user_by_id(db_path, user_id)
    if user is None:
        raise ValueError("User not found.")
    if engine == "Gemini API (Key Required)" and not api_key.strip():
        raise ValueError("Gemini API Key required for Gemini engine.")
    enforce_plan_limits(user_plan_tier(user), clean_text, srt_format, pronunciation_rules)

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = f"{safe_file_stem(file_name)}_{stamp}"
    mp3_path = output_dir / f"{stem}.mp3"
    srt_path = output_dir / f"{stem}.srt"

    if engine == "Gemini API (Key Required)":
        voice_id = gemini_voice_id_for_label(voice_label)
        duration = gemini_tts_func(
            clean_text,
            mp3_path,
            voice_id,
            gemini_model_id_for_label(gemini_model),
            api_key.strip(),
            emotion,
        )
    else:
        voice_id = edge_voice_id_for_label(voice_label)
        duration = tts_func(clean_text, mp3_path, voice_id, edge_rate(rate))
    max_chars = max_chars_for_format(srt_format)
    segments = align_text_to_duration(clean_text, duration=duration, max_chars=max_chars)
    srt_path.write_text(build_srt(segments, max_chars=80), encoding="utf-8-sig")

    record_job(
        db_path,
        user_id=user_id,
        input_chars=len(clean_text),
        voice_label=voice_label,
        mp3_path=str(mp3_path),
        srt_path=str(srt_path),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return GenerationResult(mp3_path=mp3_path, srt_path=srt_path, message="Generated MP3 and SRT.")


def generate_voice_preview(
    output_dir: Path,
    engine: str,
    voice_label: str,
    rate: int | float,
    pitch: int | float,
    volume_boost: int | float,
    emotion: str,
    api_key: str,
    gemini_model: str,
    tts_func: TtsFunc = generate_mp3,
    gemini_tts_func: GeminiTtsFunc = generate_gemini_mp3,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    mp3_path = output_dir / f"voice_preview_{stamp}.mp3"

    if engine == "Gemini API (Key Required)":
        if not api_key.strip():
            raise ValueError("Gemini API Key required for Gemini voice preview.")
        gemini_tts_func(
            voice_preview_text(voice_label),
            mp3_path,
            gemini_voice_id_for_label(voice_label),
            gemini_model_id_for_label(gemini_model),
            api_key.strip(),
            emotion,
        )
    else:
        tts_func(
            voice_preview_text(voice_label),
            mp3_path,
            edge_voice_id_for_label(voice_label),
            edge_rate(rate),
        )

    return mp3_path
