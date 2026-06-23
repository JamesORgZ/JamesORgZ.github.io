from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable

from .constants import DEFAULT_MAX_LINE_CHARS, MODEL_ID
from .media import normalize_audio
from .subtitle_formatter import build_srt
from .text_aligner import align_text_to_duration, media_duration_seconds
from .transcriber import transcribe_audio
from .tts_generator import synthesize_and_measure, voice_for_language

ProgressCallback = Callable[[str], None]


def output_srt_path(input_path: Path, output_dir: Path | None = None) -> Path:
    base_dir = output_dir if output_dir is not None else input_path.parent
    return base_dir / f"{input_path.stem}.srt"


def generate_srt(
    input_path: Path,
    output_dir: Path | None = None,
    model_path_or_id: str | Path = MODEL_ID,
    language_code: str | None = None,
    burmese_model_dir: str | Path | None = None,
    max_chars: int = DEFAULT_MAX_LINE_CHARS,
    progress: ProgressCallback | None = None,
) -> Path:
    def tell(message: str) -> None:
        if progress:
            progress(message)

    out_path = output_srt_path(input_path, output_dir)
    tell("Preparing audio with FFmpeg...")
    with tempfile.TemporaryDirectory(prefix="james_srt_") as tmp:
        wav_path = Path(tmp) / "audio.wav"
        normalize_audio(input_path, wav_path)
        tell("Transcribing original language...")
        segments, language, device = transcribe_audio(
            wav_path,
            model_path_or_id=model_path_or_id,
            language_code=language_code,
            burmese_model_dir=burmese_model_dir,
            progress=progress,
        )
        tell(f"Writing SRT ({language}, {device})...")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(build_srt(segments, max_chars=max_chars), encoding="utf-8-sig")
    tell(f"Done: {out_path}")
    return out_path


def generate_srt_from_original_text(
    input_path: Path,
    original_text: str,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> Path:
    def tell(message: str) -> None:
        if progress:
            progress(message)

    out_path = output_srt_path(input_path, output_dir)
    tell("Reading audio duration...")
    duration = media_duration_seconds(input_path)
    tell("Aligning original text to audio...")
    segments = align_text_to_duration(original_text, duration=duration, max_chars=42)
    if not segments:
        raise ValueError("Original text is empty.")
    tell("Writing SRT from original text...")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_srt(segments, max_chars=80), encoding="utf-8-sig")
    tell(f"Done: {out_path}")
    return out_path


def generate_tts_mp3_and_srt(
    text: str,
    output_dir: Path,
    base_name: str = "James_TTS",
    language_code: str | None = "my",
    progress: ProgressCallback | None = None,
) -> tuple[Path, Path]:
    def tell(message: str) -> None:
        if progress:
            progress(message)

    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Text is empty.")

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch for ch in base_name if ch.isalnum() or ch in (" ", "-", "_")).strip() or "James_TTS"
    mp3_path = output_dir / f"{safe_name}.mp3"
    srt_path = output_dir / f"{safe_name}.srt"
    voice = voice_for_language(language_code)

    tell(f"Generating MP3 with {voice}...")
    _mp3, duration = synthesize_and_measure(clean_text, mp3_path, voice=voice)
    tell("Creating SRT from original text...")
    segments = align_text_to_duration(clean_text, duration=duration, max_chars=42)
    srt_path.write_text(build_srt(segments, max_chars=80), encoding="utf-8-sig")
    tell(f"Done: {mp3_path} / {srt_path}")
    return mp3_path, srt_path
