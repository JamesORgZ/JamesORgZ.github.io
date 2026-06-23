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
        "set PYTHONPATH=%CD%\\src;%PYTHONPATH%\n"
        f"\"{sys.executable}\" -m james_srt_studio.app\n",
        encoding="utf-8",
    )

    desktop_launcher = desktop_dir() / f"{APP_NAME}.bat"
    shutil.copy2(launcher, desktop_launcher)
    return desktop_launcher


if __name__ == "__main__":
    print(install_to_desktop())
