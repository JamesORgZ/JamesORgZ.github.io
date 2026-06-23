# James SRT Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows desktop tool that converts audio/video files into accurate original-language SRT subtitles with Burmese-safe line wrapping.

**Architecture:** Create a small Python desktop app with focused core modules for formatting, FFmpeg preprocessing, faster-whisper transcription, and UI orchestration. Core subtitle logic is test-driven first, then integrated into a CustomTkinter GUI and installed to the user's Desktop with the approved James logo/theme.

**Tech Stack:** Python 3.10+, pytest, faster-whisper, CTranslate2, FFmpeg, CustomTkinter, Pillow, PyInstaller or desktop launcher scripts.

---

## File Structure

- `pyproject.toml` — package metadata, dependencies, pytest config.
- `README.md` — user setup and usage notes.
- `src/james_srt_studio/__init__.py` — package marker/version.
- `src/james_srt_studio/constants.py` — app name, paths, theme colors, supported extensions.
- `src/james_srt_studio/timecode.py` — SRT timestamp formatting.
- `src/james_srt_studio/subtitle_formatter.py` — Burmese-aware line wrapping and SRT block generation.
- `src/james_srt_studio/media.py` — FFmpeg detection and audio normalization.
- `src/james_srt_studio/transcriber.py` — faster-whisper loading, GPU/CPU fallback, transcription.
- `src/james_srt_studio/app.py` — desktop UI.
- `src/james_srt_studio/install_desktop.py` — create Desktop app folder/launcher and copy logo.
- `src/james_srt_studio/assets/logo.png` — copied user logo.
- `tests/test_timecode.py` — timestamp tests.
- `tests/test_subtitle_formatter.py` — Burmese/English line wrapping and SRT tests.
- `tests/test_media.py` — FFmpeg command/detection tests.
- `tests/test_app_smoke.py` — import/app smoke test.

## Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/james_srt_studio/__init__.py`
- Create: `src/james_srt_studio/constants.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create package metadata**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "james-srt-studio"
version = "0.1.0"
description = "Offline audio/video to SRT desktop tool for James"
requires-python = ">=3.10,<3.13"
dependencies = [
  "customtkinter>=5.2.2",
  "Pillow>=10.0.0",
  "faster-whisper>=1.1.0",
  "huggingface-hub>=0.23.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
james_srt_studio = ["assets/*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Create initial README**

Create `README.md`:

```markdown
# James SRT Studio

Windows desktop tool for converting audio/video files into `.srt` subtitle files.

Core behavior:

- Transcribes original spoken language; it does not translate.
- Uses local faster-whisper large-v3 after setup.
- Outputs standard SRT timestamps like `00:00:00,000`.
- Wraps Burmese lines safely at a maximum of 25 characters.
```

- [ ] **Step 3: Create constants**

Create `src/james_srt_studio/constants.py`:

```python
from pathlib import Path

APP_NAME = "James SRT Studio"
VERSION = "0.1.0"

THEME = {
    "background": "#050A14",
    "panel": "#081A33",
    "gold": "#FFC331",
    "gold_dark": "#C88712",
    "blue": "#04A8FF",
    "text": "#FFFFFF",
    "muted": "#9DB3C7",
}

SUPPORTED_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus",
    ".mp4", ".mkv", ".mov", ".avi", ".webm",
}

DEFAULT_MAX_LINE_CHARS = 25
MODEL_ID = "Systran/faster-whisper-large-v3"
LOCAL_MODEL_DIR_NAME = "models/faster-whisper-large-v3"


def desktop_dir() -> Path:
    return Path.home() / "Desktop"
```

- [ ] **Step 4: Create package marker**

Create `src/james_srt_studio/__init__.py`:

```python
from .constants import APP_NAME, VERSION

__all__ = ["APP_NAME", "VERSION"]
```

- [ ] **Step 5: Create pytest path sanity fixture**

Create `tests/conftest.py`:

```python
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
```

- [ ] **Step 6: Run initial test discovery**

Run:

```powershell
python -m pytest -q
```

Expected: pytest runs with no collected tests or passes once tests are added.

## Task 2: SRT Timecode Formatting

**Files:**
- Create: `src/james_srt_studio/timecode.py`
- Create: `tests/test_timecode.py`

- [ ] **Step 1: Write failing timestamp tests**

Create `tests/test_timecode.py`:

```python
from james_srt_studio.timecode import format_srt_timestamp


def test_zero_timestamp():
    assert format_srt_timestamp(0) == "00:00:00,000"


def test_timestamp_with_hours_minutes_seconds_and_milliseconds():
    assert format_srt_timestamp(3723.456) == "01:02:03,456"


def test_timestamp_rounds_to_nearest_millisecond():
    assert format_srt_timestamp(1.9996) == "00:00:02,000"


def test_negative_timestamp_clamps_to_zero():
    assert format_srt_timestamp(-2.5) == "00:00:00,000"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_timecode.py -q
```

Expected: FAIL because `james_srt_studio.timecode` does not exist.

- [ ] **Step 3: Implement timestamp formatter**

Create `src/james_srt_studio/timecode.py`:

```python
def format_srt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/test_timecode.py -q
```

Expected: PASS.

## Task 3: Burmese-Safe Line Wrapping

**Files:**
- Create: `src/james_srt_studio/subtitle_formatter.py`
- Create: `tests/test_subtitle_formatter.py`

- [ ] **Step 1: Write failing line wrapping tests**

Create `tests/test_subtitle_formatter.py`:

```python
from james_srt_studio.subtitle_formatter import wrap_subtitle_text


def test_burmese_phrase_split_matches_user_example():
    text = "မောင်မောင်ကနေမကောင်းလို့အပြင်မသွားဘူး"
    assert wrap_subtitle_text(text, max_chars=25) == [
        "မောင်မောင်ကနေမကောင်းလို့",
        "အပြင်မသွားဘူး",
    ]


def test_burmese_combining_marks_stay_attached():
    text = "မောင်မောင်ကနေမကောင်းလို့အပြင်မသွားဘူး"
    lines = wrap_subtitle_text(text, max_chars=12)
    assert "".join(lines) == text
    for line in lines:
        assert not line.startswith(("ါ", "ာ", "ိ", "ီ", "ု", "ူ", "ေ", "ဲ", "ံ", "့", "း", "်", "ျ", "ြ", "ွ", "ှ"))


def test_english_wraps_on_spaces():
    assert wrap_subtitle_text("James goes to the cinema today", max_chars=12) == [
        "James goes",
        "to the",
        "cinema today",
    ]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_subtitle_formatter.py -q
```

Expected: FAIL because `subtitle_formatter` does not exist.

- [ ] **Step 3: Implement Burmese-safe wrapper**

Create `src/james_srt_studio/subtitle_formatter.py`:

```python
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
    "က",
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


def _cluster_len(text: str) -> int:
    return len(_safe_clusters(text))


def _find_preferred_burmese_split(text: str, max_chars: int) -> int | None:
    best: int | None = None
    for ending in BURMESE_PHRASE_ENDINGS:
        search_from = 0
        while True:
            idx = text.find(ending, search_from)
            if idx == -1:
                break
            split_at = idx + len(ending)
            if 0 < _cluster_len(text[:split_at]) <= max_chars:
                best = split_at if best is None else max(best, split_at)
            search_from = idx + 1
    return best


def _split_long_cluster_safe(text: str, max_chars: int) -> tuple[str, str]:
    clusters = _safe_clusters(text)
    left = "".join(clusters[:max_chars])
    right = "".join(clusters[max_chars:])
    return left, right


def _wrap_unspaced_text(text: str, max_chars: int) -> list[str]:
    lines: list[str] = []
    remaining = text
    while _cluster_len(remaining) > max_chars:
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
        if _cluster_len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        if _cluster_len(word) > max_chars:
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
    for index, segment in enumerate(segments, start=1):
        lines = wrap_subtitle_text(segment.text, max_chars=max_chars)
        if not lines:
            continue
        block = [
            str(index),
            f"{format_srt_timestamp(segment.start)} --> {format_srt_timestamp(segment.end)}",
            *lines,
        ]
        blocks.append("\n".join(block))
    return "\n\n".join(blocks) + ("\n" if blocks else "")
```

- [ ] **Step 4: Run line wrapping tests**

Run:

```powershell
python -m pytest tests/test_subtitle_formatter.py -q
```

Expected: PASS.

## Task 4: SRT Writer Behavior

**Files:**
- Modify: `tests/test_subtitle_formatter.py`
- Modify: `src/james_srt_studio/subtitle_formatter.py`

- [ ] **Step 1: Add SRT writer test**

Append to `tests/test_subtitle_formatter.py`:

```python
from james_srt_studio.subtitle_formatter import SubtitleSegment, build_srt


def test_build_srt_uses_standard_timestamp_and_wrapped_text():
    srt = build_srt([
        SubtitleSegment(0, 3.5, "မောင်မောင်ကနေမကောင်းလို့အပြင်မသွားဘူး"),
    ], max_chars=25)
    assert srt == (
        "1\n"
        "00:00:00,000 --> 00:00:03,500\n"
        "မောင်မောင်ကနေမကောင်းလို့\n"
        "အပြင်မသွားဘူး\n"
    )
```

- [ ] **Step 2: Run SRT writer test**

Run:

```powershell
python -m pytest tests/test_subtitle_formatter.py::test_build_srt_uses_standard_timestamp_and_wrapped_text -q
```

Expected: PASS if Task 3 implementation already included `build_srt`; otherwise FAIL and then add the shown `build_srt` function from Task 3.

- [ ] **Step 3: Run all core formatter tests**

Run:

```powershell
python -m pytest tests/test_timecode.py tests/test_subtitle_formatter.py -q
```

Expected: PASS.

## Task 5: Media Preprocessing with FFmpeg

**Files:**
- Create: `src/james_srt_studio/media.py`
- Create: `tests/test_media.py`

- [ ] **Step 1: Write FFmpeg command tests**

Create `tests/test_media.py`:

```python
from pathlib import Path

from james_srt_studio.media import build_ffmpeg_command, is_supported_media


def test_supported_media_extensions():
    assert is_supported_media(Path("voice.mp3"))
    assert is_supported_media(Path("movie.mp4"))
    assert not is_supported_media(Path("notes.txt"))


def test_build_ffmpeg_command_normalizes_to_16khz_mono_wav():
    cmd = build_ffmpeg_command(Path("input.mp4"), Path("work.wav"))
    assert cmd == [
        "ffmpeg",
        "-y",
        "-i",
        "input.mp4",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-acodec",
        "pcm_s16le",
        "work.wav",
    ]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_media.py -q
```

Expected: FAIL because `media.py` does not exist.

- [ ] **Step 3: Implement media helpers**

Create `src/james_srt_studio/media.py`:

```python
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
```

- [ ] **Step 4: Run media tests**

Run:

```powershell
python -m pytest tests/test_media.py -q
```

Expected: PASS.

## Task 6: Faster Whisper Transcriber

**Files:**
- Create: `src/james_srt_studio/transcriber.py`
- Create: `tests/test_transcriber.py`

- [ ] **Step 1: Write transcriber mapping tests without loading the model**

Create `tests/test_transcriber.py`:

```python
from types import SimpleNamespace

from james_srt_studio.transcriber import whisper_segments_to_subtitle_segments


def test_whisper_segments_convert_to_subtitle_segments():
    whisper_segments = [
        SimpleNamespace(start=0.0, end=1.25, text=" Hello "),
        SimpleNamespace(start=1.25, end=2.5, text="မင်္ဂလာပါ"),
    ]
    result = whisper_segments_to_subtitle_segments(whisper_segments)
    assert [(s.start, s.end, s.text) for s in result] == [
        (0.0, 1.25, "Hello"),
        (1.25, 2.5, "မင်္ဂလာပါ"),
    ]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_transcriber.py -q
```

Expected: FAIL because `transcriber.py` does not exist.

- [ ] **Step 3: Implement transcriber with GPU/CPU fallback**

Create `src/james_srt_studio/transcriber.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .constants import MODEL_ID
from .subtitle_formatter import SubtitleSegment


class TranscriptionError(RuntimeError):
    pass


def whisper_segments_to_subtitle_segments(segments: Iterable[object]) -> list[SubtitleSegment]:
    result: list[SubtitleSegment] = []
    for segment in segments:
        text = str(getattr(segment, "text", "")).strip()
        if not text:
            continue
        result.append(SubtitleSegment(
            start=float(getattr(segment, "start")),
            end=float(getattr(segment, "end")),
            text=text,
        ))
    return result


def _load_model(model_path_or_id: str | Path, device: str, compute_type: str):
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


def transcribe_audio(audio_path: Path, model_path_or_id: str | Path = MODEL_ID) -> tuple[list[SubtitleSegment], str, str]:
    model, device = load_best_model(model_path_or_id)
    segments, info = model.transcribe(
        str(audio_path),
        task="transcribe",
        language=None,
        vad_filter=True,
        word_timestamps=True,
        beam_size=5,
    )
    subtitle_segments = whisper_segments_to_subtitle_segments(segments)
    language = getattr(info, "language", "unknown")
    return subtitle_segments, language, device
```

- [ ] **Step 4: Run transcriber unit tests**

Run:

```powershell
python -m pytest tests/test_transcriber.py -q
```

Expected: PASS.

## Task 7: End-to-End Core Pipeline

**Files:**
- Create: `src/james_srt_studio/pipeline.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Write pipeline test with monkeypatched dependencies**

Create `tests/test_pipeline.py`:

```python
from pathlib import Path

from james_srt_studio.pipeline import output_srt_path


def test_output_srt_path_replaces_extension():
    assert output_srt_path(Path(r"C:\Audio\voice.mp3")) == Path(r"C:\Audio\voice.srt")
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_pipeline.py -q
```

Expected: FAIL because `pipeline.py` does not exist.

- [ ] **Step 3: Implement pipeline**

Create `src/james_srt_studio/pipeline.py`:

```python
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable

from .constants import DEFAULT_MAX_LINE_CHARS, MODEL_ID
from .media import normalize_audio
from .subtitle_formatter import build_srt
from .transcriber import transcribe_audio

ProgressCallback = Callable[[str], None]


def output_srt_path(input_path: Path, output_dir: Path | None = None) -> Path:
    base_dir = output_dir if output_dir is not None else input_path.parent
    return base_dir / f"{input_path.stem}.srt"


def generate_srt(
    input_path: Path,
    output_dir: Path | None = None,
    model_path_or_id: str | Path = MODEL_ID,
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
        segments, language, device = transcribe_audio(wav_path, model_path_or_id=model_path_or_id)
        tell(f"Writing SRT ({language}, {device})...")
        out_path.write_text(build_srt(segments, max_chars=max_chars), encoding="utf-8-sig")
    tell(f"Done: {out_path}")
    return out_path
```

- [ ] **Step 4: Run pipeline tests**

Run:

```powershell
python -m pytest tests/test_pipeline.py -q
```

Expected: PASS.

## Task 8: Desktop UI

**Files:**
- Create: `src/james_srt_studio/app.py`
- Create: `tests/test_app_smoke.py`
- Copy: `C:\Users\James\Desktop\Logo\Jamesrecap\Picsart_26-04-09_21-45-34-093.png` to `src/james_srt_studio/assets/logo.png`

- [ ] **Step 1: Write app smoke test**

Create `tests/test_app_smoke.py`:

```python
def test_app_module_imports():
    import james_srt_studio.app as app

    assert app.main is not None
```

- [ ] **Step 2: Run smoke test to verify failure**

Run:

```powershell
python -m pytest tests/test_app_smoke.py -q
```

Expected: FAIL because `app.py` does not exist.

- [ ] **Step 3: Copy logo asset**

Run:

```powershell
New-Item -ItemType Directory -Force src\james_srt_studio\assets
Copy-Item "C:\Users\James\Desktop\Logo\Jamesrecap\Picsart_26-04-09_21-45-34-093.png" src\james_srt_studio\assets\logo.png -Force
```

Expected: `src\james_srt_studio\assets\logo.png` exists.

- [ ] **Step 4: Implement CustomTkinter UI**

Create `src/james_srt_studio/app.py`:

```python
from __future__ import annotations

import queue
import threading
from importlib.resources import files
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from .constants import APP_NAME, DEFAULT_MAX_LINE_CHARS, SUPPORTED_EXTENSIONS, THEME
from .pipeline import generate_srt


class JamesSrtApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("900x640")
        self.configure(fg_color=THEME["background"])
        ctk.set_appearance_mode("dark")
        self.selected_file: Path | None = None
        self.events: queue.Queue[tuple[str, str]] = queue.Queue()
        self._build_ui()
        self.after(200, self._poll_events)

    def _build_ui(self) -> None:
        root = ctk.CTkFrame(self, fg_color=THEME["background"])
        root.pack(fill="both", expand=True, padx=24, pady=24)

        logo_path = files("james_srt_studio").joinpath("assets/logo.png")
        if logo_path.is_file():
            image = ctk.CTkImage(Image.open(logo_path), size=(110, 110))
            ctk.CTkLabel(root, image=image, text="").pack(pady=(0, 8))

        ctk.CTkLabel(
            root,
            text=APP_NAME,
            text_color=THEME["gold"],
            font=("Segoe UI", 32, "bold"),
        ).pack()

        ctk.CTkLabel(
            root,
            text="Audio/Video ထည့်လိုက်တာနဲ့ original language အတိုင်း SRT ထုတ်ပေးမယ်",
            text_color=THEME["muted"],
            font=("Segoe UI", 15),
        ).pack(pady=(4, 20))

        self.file_label = ctk.CTkLabel(
            root,
            text="No file selected",
            text_color=THEME["text"],
            fg_color=THEME["panel"],
            corner_radius=16,
            height=74,
            font=("Segoe UI", 16),
        )
        self.file_label.pack(fill="x", pady=(0, 12))

        ctk.CTkButton(
            root,
            text="Browse Audio/Video",
            command=self._browse_file,
            fg_color=THEME["gold_dark"],
            hover_color=THEME["gold"],
            text_color="#06101E",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(0, 14))

        settings = ctk.CTkFrame(root, fg_color=THEME["panel"], corner_radius=16)
        settings.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(settings, text="Language: Auto Detect  •  Model: Large V3 Accurate  •  Max line: 25", text_color=THEME["text"]).pack(padx=18, pady=14)

        self.generate_button = ctk.CTkButton(
            root,
            text="Generate SRT",
            command=self._start_generation,
            fg_color=THEME["blue"],
            hover_color=THEME["gold"],
            text_color="#06101E",
            height=44,
            font=("Segoe UI", 18, "bold"),
        )
        self.generate_button.pack(fill="x", pady=(0, 12))

        self.progress = ctk.CTkProgressBar(root, progress_color=THEME["gold"])
        self.progress.set(0)
        self.progress.pack(fill="x", pady=(0, 10))

        self.status_label = ctk.CTkLabel(root, text="Ready", text_color=THEME["muted"])
        self.status_label.pack(anchor="w")

        self.preview = ctk.CTkTextbox(root, fg_color="#020712", text_color=THEME["text"], height=210)
        self.preview.pack(fill="both", expand=True, pady=(10, 0))
        self.preview.insert("1.0", "SRT preview will appear here...")

    def _browse_file(self) -> None:
        patterns = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
        filename = filedialog.askopenfilename(title="Choose audio/video", filetypes=[("Media files", patterns), ("All files", "*.*")])
        if filename:
            self.selected_file = Path(filename)
            self.file_label.configure(text=str(self.selected_file))

    def _start_generation(self) -> None:
        if self.selected_file is None:
            messagebox.showwarning(APP_NAME, "Audio/video file အရင်ရွေးပါ။")
            return
        self.generate_button.configure(state="disabled")
        self.progress.set(0.15)
        self.status_label.configure(text="Starting...")
        thread = threading.Thread(target=self._run_generation, daemon=True)
        thread.start()

    def _run_generation(self) -> None:
        try:
            out_path = generate_srt(
                self.selected_file,
                max_chars=DEFAULT_MAX_LINE_CHARS,
                progress=lambda message: self.events.put(("status", message)),
            )
            self.events.put(("done", str(out_path)))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _poll_events(self) -> None:
        while not self.events.empty():
            kind, message = self.events.get_nowait()
            if kind == "status":
                self.status_label.configure(text=message)
                self.progress.set(min(0.85, self.progress.get() + 0.15))
            elif kind == "done":
                self.progress.set(1)
                self.status_label.configure(text=f"Done: {message}")
                self.generate_button.configure(state="normal")
                out_path = Path(message)
                if out_path.exists():
                    self.preview.delete("1.0", "end")
                    self.preview.insert("1.0", out_path.read_text(encoding="utf-8-sig")[:4000])
            elif kind == "error":
                self.progress.set(0)
                self.status_label.configure(text="Error")
                self.generate_button.configure(state="normal")
                messagebox.showerror(APP_NAME, message)
        self.after(200, self._poll_events)


def main() -> None:
    app = JamesSrtApp()
    app.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run app smoke test**

Run:

```powershell
python -m pytest tests/test_app_smoke.py -q
```

Expected: PASS.

## Task 9: Model Setup and Offline Cache

**Files:**
- Create: `src/james_srt_studio/model_setup.py`
- Modify: `src/james_srt_studio/transcriber.py`

- [ ] **Step 1: Implement model setup helper**

Create `src/james_srt_studio/model_setup.py`:

```python
from __future__ import annotations

from pathlib import Path

from huggingface_hub import snapshot_download

from .constants import LOCAL_MODEL_DIR_NAME, MODEL_ID


def default_model_dir(base_dir: Path | None = None) -> Path:
    root = base_dir if base_dir is not None else Path(__file__).resolve().parents[2]
    return root / LOCAL_MODEL_DIR_NAME


def model_exists(model_dir: Path) -> bool:
    return model_dir.exists() and any(model_dir.iterdir())


def ensure_model(model_dir: Path | None = None) -> Path:
    target = model_dir or default_model_dir()
    if model_exists(target):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=MODEL_ID, local_dir=target, local_dir_use_symlinks=False)
    return target
```

- [ ] **Step 2: Use local model by default in UI pipeline**

Modify `src/james_srt_studio/app.py` `_run_generation` to call `ensure_model()` before `generate_srt`:

```python
from .model_setup import ensure_model
```

and:

```python
model_dir = ensure_model()
out_path = generate_srt(
    self.selected_file,
    model_path_or_id=model_dir,
    max_chars=DEFAULT_MAX_LINE_CHARS,
    progress=lambda message: self.events.put(("status", message)),
)
```

- [ ] **Step 3: Run non-model tests**

Run:

```powershell
python -m pytest tests -q
```

Expected: PASS. These tests must not download or load the model.

## Task 10: Desktop Installation

**Files:**
- Create: `src/james_srt_studio/install_desktop.py`
- Create: `James SRT Studio.bat` in Desktop app folder during execution

- [ ] **Step 1: Implement desktop installer**

Create `src/james_srt_studio/install_desktop.py`:

```python
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .constants import APP_NAME, desktop_dir


def install_to_desktop(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parents[2]
    install_dir = desktop_dir() / APP_NAME
    install_dir.mkdir(parents=True, exist_ok=True)
    launcher = install_dir / f"{APP_NAME}.bat"
    launcher.write_text(
        "@echo off\n"
        f"cd /d \"{root}\"\n"
        f"\"{sys.executable}\" -m james_srt_studio.app\n",
        encoding="utf-8",
    )
    desktop_launcher = desktop_dir() / f"{APP_NAME}.bat"
    shutil.copy2(launcher, desktop_launcher)
    return desktop_launcher


if __name__ == "__main__":
    print(install_to_desktop())
```

- [ ] **Step 2: Run installer**

Run:

```powershell
python -m james_srt_studio.install_desktop
```

Expected: `C:\Users\James\Desktop\James SRT Studio.bat` exists.

## Task 11: Verification

**Files:**
- No new files unless fixes are needed.

- [ ] **Step 1: Run full unit tests**

Run:

```powershell
python -m pytest tests -q
```

Expected: PASS.

- [ ] **Step 2: Check FFmpeg**

Run:

```powershell
ffmpeg -version
```

Expected: FFmpeg version is printed.

- [ ] **Step 3: Launch app import smoke**

Run:

```powershell
python -c "from james_srt_studio.app import main; print('app import ok')"
```

Expected: `app import ok`.

- [ ] **Step 4: Optional real transcription smoke test**

If a short sample audio file is available, run the app on it and confirm:

- `.srt` file is created.
- timestamps use `00:00:00,000`.
- Burmese lines are not broken inside syllables/marks.
- output language is the spoken language.

## Self-Review Notes

- Spec coverage: plan covers desktop app, logo/theme, offline model cache, original-language transcription, SRT timestamp format, Burmese-safe line wrapping, FFmpeg preprocessing, GPU/CPU fallback, and Desktop launcher.
- Placeholder scan: no unresolved placeholder wording or vague deferred implementation steps.
- Type consistency: `SubtitleSegment`, `wrap_subtitle_text`, `build_srt`, `generate_srt`, and `ensure_model` names are consistent across tasks.
- Git note: this workspace is not currently a git repository, so commit steps are omitted. If a git repo is initialized later, commit after each task.
