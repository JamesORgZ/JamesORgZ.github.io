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
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".opus",
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".webm",
}

DEFAULT_MAX_LINE_CHARS = 25
MODEL_ID = "Systran/faster-whisper-large-v3"
LOCAL_MODEL_DIR_NAME = "models/faster-whisper-large-v3"
BURMESE_ASR_MODEL_ID = "myatsu/whisper-small-burmese-v3"
LOCAL_BURMESE_ASR_MODEL_DIR_NAME = "models/faster-whisper-small-burmese-v3"


def desktop_dir() -> Path:
    return Path.home() / "Desktop"
