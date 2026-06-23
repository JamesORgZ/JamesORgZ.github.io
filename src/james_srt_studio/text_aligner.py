from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .subtitle_formatter import SubtitleSegment

TIMESTAMP_RE = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})")
INDEX_RE = re.compile(r"^\s*\d+\s*$")
MYANMAR_PREFERRED_ENDINGS = (
    "တယ်",
    "တယ်။",
    "ပါတယ်",
    "ပါတယ်။",
    "လိုက်တယ်",
    "လိုက်တယ်။",
    "မယ်",
    "မယ်။",
    "တော့",
    "ပြီး",
    "ကာ",
    "မှာ",
    "ကို",
    "လို့",
    "တဲ့",
)


def media_duration_seconds(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nk=1:nw=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Could not read media duration.")
    return max(0.001, float(completed.stdout.strip()))


def strip_srt_to_text(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if INDEX_RE.match(line):
            continue
        if TIMESTAMP_RE.search(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def _parse_timestamp(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return (int(hours) * 3600) + (int(minutes) * 60) + int(seconds) + (int(millis) / 1000)


def parse_srt_segments(text: str) -> list[SubtitleSegment]:
    segments: list[SubtitleSegment] = []
    current_start: float | None = None
    current_end: float | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_start, current_end, current_lines
        if current_start is not None and current_end is not None and current_lines:
            segments.append(SubtitleSegment(current_start, current_end, " ".join(current_lines).strip()))
        current_start = None
        current_end = None
        current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if INDEX_RE.match(line):
            continue
        match = TIMESTAMP_RE.search(line)
        if match:
            flush()
            current_start = _parse_timestamp(match.group(1))
            current_end = _parse_timestamp(match.group(2))
            continue
        if current_start is not None:
            current_lines.append(line)
    flush()
    return segments


def normalize_original_text(text: str) -> str:
    cleaned = strip_srt_to_text(text)
    return "\n".join(" ".join(line.split()) for line in cleaned.splitlines() if line.strip())


def _split_long_unspaced(text: str, max_chars: int) -> list[str]:
    chunks: list[str] = []
    remaining = text.strip()
    while len(remaining) > max_chars:
        split_at: int | None = None
        search_limit = min(len(remaining), max_chars)
        for ending in MYANMAR_PREFERRED_ENDINGS:
            idx = remaining.rfind(ending, 0, search_limit + 1)
            if idx > 0:
                split_at = idx + len(ending)
                break
        if split_at is None or split_at < max(8, max_chars // 3):
            split_at = search_limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def split_original_text(text: str, max_chars: int = 42) -> list[str]:
    normalized = normalize_original_text(text)
    if not normalized:
        return []

    rough_parts: list[str] = []
    for line in normalized.splitlines():
        pieces = re.split(r"(?<=[။!?])\s*", line)
        rough_parts.extend(piece.strip() for piece in pieces if piece.strip())

    final_parts: list[str] = []
    for part in rough_parts:
        if " " in part:
            current = ""
            for word in part.split():
                candidate = word if not current else f"{current} {word}"
                if len(candidate) <= max_chars:
                    current = candidate
                else:
                    if current:
                        final_parts.append(current)
                    current = word
            if current:
                final_parts.append(current)
        else:
            final_parts.extend(_split_long_unspaced(part, max_chars=max_chars))
    return [part for part in final_parts if part]


def _weight(text: str) -> float:
    myanmar_chars = sum(1 for ch in text if "\u1000" <= ch <= "\u109f")
    other_chars = max(0, len(text) - myanmar_chars)
    return max(1.0, myanmar_chars + (other_chars * 0.45))


def align_text_to_duration(text: str, duration: float, max_chars: int = 42) -> list[SubtitleSegment]:
    parsed_srt = parse_srt_segments(text)
    if parsed_srt:
        return parsed_srt
    parts = split_original_text(text, max_chars=max_chars)
    if not parts:
        return []
    total_weight = sum(_weight(part) for part in parts)
    cursor = 0.0
    segments: list[SubtitleSegment] = []
    for index, part in enumerate(parts, start=1):
        if index == len(parts):
            end = duration
        else:
            end = cursor + (duration * (_weight(part) / total_weight))
        if end <= cursor:
            end = min(duration, cursor + 0.25)
        segments.append(SubtitleSegment(start=cursor, end=end, text=part))
        cursor = end
    return segments
