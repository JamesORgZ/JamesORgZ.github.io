from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

from .text_aligner import media_duration_seconds

DEFAULT_MYANMAR_VOICE = "my-MM-NilarNeural"
DEFAULT_ENGLISH_VOICE = "en-US-JennyNeural"


def voice_for_language(language_code: str | None) -> str:
    if language_code == "my":
        return DEFAULT_MYANMAR_VOICE
    if language_code == "en":
        return DEFAULT_ENGLISH_VOICE
    return DEFAULT_MYANMAR_VOICE


async def _synthesize_async(text: str, out_mp3: Path, voice: str, rate: str = "+0%") -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(out_mp3))


def synthesize_to_mp3(text: str, out_mp3: Path, voice: str, rate: str = "+0%") -> Path:
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize_async(text=text, out_mp3=out_mp3, voice=voice, rate=rate))
    if not out_mp3.exists() or out_mp3.stat().st_size == 0:
        raise RuntimeError("TTS failed to create MP3 output.")
    return out_mp3


def synthesize_and_measure(text: str, out_mp3: Path, voice: str, rate: str = "+0%") -> tuple[Path, float]:
    mp3_path = synthesize_to_mp3(text=text, out_mp3=out_mp3, voice=voice, rate=rate)
    return mp3_path, media_duration_seconds(mp3_path)
