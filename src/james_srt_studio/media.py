from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .constants import SUPPORTED_EXTENSIONS


class MediaError(RuntimeError):
    pass


def is_supported_media(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def build_ffmpeg_command(input_path: Path, output_wav: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-acodec",
        "pcm_s16le",
        str(output_wav),
    ]


def normalize_audio(input_path: Path, output_wav: Path) -> Path:
    if not input_path.exists():
        raise MediaError(f"File not found: {input_path}")
    if not is_supported_media(input_path):
        raise MediaError(f"Unsupported file type: {input_path.suffix}")
    if not ffmpeg_available():
        raise MediaError("FFmpeg is not installed or not available in PATH.")
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        build_ffmpeg_command(input_path, output_wav),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise MediaError(completed.stderr.strip() or "FFmpeg failed to read this media file.")
    return output_wav
