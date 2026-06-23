from __future__ import annotations

import sys
from pathlib import Path

from huggingface_hub import snapshot_download

from .constants import (
    BURMESE_ASR_MODEL_ID,
    LOCAL_BURMESE_ASR_MODEL_DIR_NAME,
    LOCAL_MODEL_DIR_NAME,
    MODEL_ID,
)


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def default_model_dir(base_dir: Path | None = None) -> Path:
    root = base_dir if base_dir is not None else project_root()
    return root / LOCAL_MODEL_DIR_NAME


def default_burmese_asr_model_dir(base_dir: Path | None = None) -> Path:
    root = base_dir if base_dir is not None else project_root()
    return root / LOCAL_BURMESE_ASR_MODEL_DIR_NAME


def model_exists(model_dir: Path) -> bool:
    return model_dir.exists() and any(model_dir.iterdir())


def ensure_model(model_dir: Path | None = None, progress=None) -> Path:
    target = model_dir or default_model_dir()
    if model_exists(target):
        return target
    if progress:
        progress("Downloading large-v3 model for offline use. This can take a while...")
    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=MODEL_ID, local_dir=target, local_dir_use_symlinks=False)
    return target


def ensure_burmese_asr_model(model_dir: Path | None = None, progress=None) -> Path:
    target = model_dir or default_burmese_asr_model_dir()
    if model_exists(target):
        return target
    raise FileNotFoundError(
        f"Burmese Unicode model is missing: {target}. "
        "Reinstall the app folder so the bundled Burmese model is present."
    )
