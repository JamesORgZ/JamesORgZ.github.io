from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "James Audio & Srt Generator"
DEFAULT_ADMIN_PIN = os.getenv("JAMES_WEB_ADMIN_PIN", "556945")
DEFAULT_LOGO_PATH = Path(r"C:\Users\James\Downloads\Telegram Desktop\photo_2026-06-22_18-57-59.jpg")


def default_data_dir() -> Path:
    configured = os.getenv("JAMES_WEB_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.cwd() / "web_data").resolve()


def default_db_path() -> Path:
    return default_data_dir() / "james_web_tool.sqlite3"


def default_output_dir() -> Path:
    return default_data_dir() / "outputs"


def default_logo_path() -> Path:
    configured = os.getenv("JAMES_WEB_LOGO_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_LOGO_PATH
