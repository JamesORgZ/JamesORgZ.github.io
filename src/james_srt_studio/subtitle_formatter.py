from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .constants import DEFAULT_MAX_LINE_CHARS
from .timecode import format_srt_timestamp

MYANMAR_COMBINING_OR_JOINING = set(
    "\u102B\u102C\u102D\u102E\u102F\u1030\u1031\u1032\u1036\u1037\u1038"
    "\u1039\u103A\u103B\u103C\u103D\u103E\u1056\u1057\u1062\u1063\u1064"
    "\u1067\u1068\u1069\u106A\u106B\u106C\u106D\u1071\u1072\u1073\u1074"
    "\u1082\u1083\u1084\u1085\u1086\u1087\u1088\u1089\u108A\u109A\u109B\u109C"
)

BURMESE_PHRASE_ENDINGS = [
    "လို့",
    "တော့",
    "ပြီး",
    "တာ",
    "တယ်",
    "မယ်",
    "ပါ",
    "ခဲ့",
    "မှာ",
    "ကို",
]


@dataclass(frozen=True)
class SubtitleSegment:
    start: float
    end: float
    text: str


def _is_myanmar_mark(ch: str) -> bool:
    return ch in MYANMAR_COMBINING_OR_JOINING


def _safe_clusters(text: str) -> list[str]:
    clusters: list[str] = []
    for ch in text:
        if clusters and _is_myanmar_mark(ch):
            clusters[-1] += ch
        else:
            clusters.append(ch)
    return clusters


def _text_len(text: str) -> int:
    return len(text)


def _find_preferred_burmese_split(text: str, max_chars: int) -> int | None:
    best: int | None = None
    for ending in BURMESE_PHRASE_ENDINGS:
        search_from = 0
        while True:
            idx = text.find(ending, search_from)
            if idx == -1:
                break
            split_at = idx + len(ending)
            next_starts_with_mark = split_at < len(text) and _is_myanmar_mark(text[split_at])
            if 0 < _text_len(text[:split_at]) <= max_chars and not next_starts_with_mark:
                best = split_at if best is None else max(best, split_at)
            search_from = idx + 1
    return best


def _split_long_cluster_safe(text: str, max_chars: int) -> tuple[str, str]:
    clusters = _safe_clusters(text)
    left_clusters: list[str] = []
    used = 0
    for cluster in clusters:
        next_used = used + len(cluster)
        if left_clusters and next_used > max_chars:
            break
        left_clusters.append(cluster)
        used = next_used
    if not left_clusters:
        left_clusters = [clusters[0]]
    split_index = len(left_clusters)
    left = "".join(left_clusters)
    right = "".join(clusters[split_index:])
    return left, right


def _wrap_unspaced_text(text: str, max_chars: int) -> list[str]:
    lines: list[str] = []
    remaining = text
    while _text_len(remaining) > max_chars:
        split_at = _find_preferred_burmese_split(remaining, max_chars)
        if split_at is None:
            left, remaining = _split_long_cluster_safe(remaining, max_chars)
        else:
            left, remaining = remaining[:split_at], remaining[split_at:]
        if left:
            lines.append(left)
        remaining = remaining.lstrip()
    if remaining:
        lines.append(remaining)
    return lines


def _wrap_spaced_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if _text_len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        if _text_len(word) > max_chars:
            lines.extend(_wrap_unspaced_text(word, max_chars))
            current = ""
        else:
            current = word
    if current:
        lines.append(current)
    return lines


def wrap_subtitle_text(text: str, max_chars: int = DEFAULT_MAX_LINE_CHARS) -> list[str]:
    clean = " ".join(text.strip().split())
    if not clean:
        return []
    if " " in clean:
        return _wrap_spaced_text(clean, max_chars)
    return _wrap_unspaced_text(clean, max_chars)


def build_srt(segments: Iterable[SubtitleSegment], max_chars: int = DEFAULT_MAX_LINE_CHARS) -> str:
    blocks: list[str] = []
    output_index = 1
    for segment in segments:
        lines = wrap_subtitle_text(segment.text, max_chars=max_chars)
        if not lines:
            continue
        block = [
            str(output_index),
            f"{format_srt_timestamp(segment.start)} --> {format_srt_timestamp(segment.end)}",
            *lines,
        ]
        blocks.append("\n".join(block))
        output_index += 1
    return "\n\n".join(blocks) + ("\n" if blocks else "")
