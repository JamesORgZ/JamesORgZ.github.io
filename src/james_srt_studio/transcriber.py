from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

from .constants import MODEL_ID
from .constants import DEFAULT_MAX_LINE_CHARS
from .subtitle_formatter import SubtitleSegment, wrap_subtitle_text


class TranscriptionError(RuntimeError):
    pass


def _bootstrap_nvidia_dll_paths() -> None:
    candidates: list[Path] = []
    roots = [
        Path(__file__).resolve().parents[2] / "work" / "nvidia",
        Path(__file__).resolve().parents[2] / "nvidia",
    ]
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        internal_dir = Path(getattr(sys, "_MEIPASS", exe_dir))
        roots.extend([exe_dir / "nvidia", internal_dir / "nvidia"])
    for root in roots:
        if root.exists():
            candidates.extend(path for path in root.glob("*\\bin") if path.is_dir())
    for path in candidates:
        os.environ["PATH"] = f"{path}{os.pathsep}{os.environ.get('PATH', '')}"
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(path))


def whisper_segments_to_subtitle_segments(segments: Iterable[object]) -> list[SubtitleSegment]:
    result: list[SubtitleSegment] = []
    for segment in segments:
        text = str(getattr(segment, "text", "")).replace("�", "").strip()
        if not text:
            continue
        result.append(
            SubtitleSegment(
                start=float(getattr(segment, "start")),
                end=float(getattr(segment, "end")),
                text=text,
            )
        )
    return result


def split_long_segments(
    segments: Iterable[SubtitleSegment],
    max_chars: int = DEFAULT_MAX_LINE_CHARS,
    max_duration: float = 8.0,
) -> list[SubtitleSegment]:
    output: list[SubtitleSegment] = []
    for segment in segments:
        lines = wrap_subtitle_text(segment.text, max_chars=max_chars)
        duration = max(0.0, segment.end - segment.start)
        if len(lines) <= 1 and duration <= max_duration:
            output.append(segment)
            continue
        if not lines:
            continue
        step = duration / len(lines) if duration > 0 else 0
        for index, line in enumerate(lines):
            start = segment.start + (step * index)
            end = segment.start + (step * (index + 1))
            output.append(SubtitleSegment(start=start, end=end, text=line))
    return output


def _load_model(model_path_or_id: str | Path, device: str, compute_type: str):
    _bootstrap_nvidia_dll_paths()
    from faster_whisper import WhisperModel

    return WhisperModel(str(model_path_or_id), device=device, compute_type=compute_type)


def load_best_model(model_path_or_id: str | Path = MODEL_ID):
    try:
        return _load_model(model_path_or_id, device="cuda", compute_type="float16"), "cuda"
    except Exception as cuda_error:
        try:
            return _load_model(model_path_or_id, device="cpu", compute_type="int8"), "cpu"
        except Exception as cpu_error:
            raise TranscriptionError(
                f"Could not load Whisper model. CUDA error: {cuda_error}; CPU error: {cpu_error}"
            ) from cpu_error


def transcribe_audio(
    audio_path: Path,
    model_path_or_id: str | Path = MODEL_ID,
    language_code: str | None = None,
    burmese_model_dir: str | Path | None = None,
    progress=None,
) -> tuple[list[SubtitleSegment], str, str]:
    if language_code == "my":
        if burmese_model_dir is None:
            raise TranscriptionError("Burmese ASR model path is required for Burmese mode.")
        if progress:
            progress("Transcribing Burmese Unicode with GPU model...")
        model, device = load_best_model(burmese_model_dir)
        segments, _ = model.transcribe(
            str(audio_path),
            task="transcribe",
            language="my",
            vad_filter=True,
            word_timestamps=False,
            beam_size=5,
            condition_on_previous_text=False,
        )
        subtitle_segments = split_long_segments(whisper_segments_to_subtitle_segments(segments))
        return subtitle_segments, "my", f"burmese-{device}"

    model, device = load_best_model(model_path_or_id)
    segments, info = model.transcribe(
        str(audio_path),
        task="transcribe",
        language=language_code,
        vad_filter=True,
        word_timestamps=True,
        beam_size=5,
    )
    subtitle_segments = whisper_segments_to_subtitle_segments(segments)
    language = getattr(info, "language", "unknown")
    return subtitle_segments, language, device
