from __future__ import annotations

import os
import sys
from pathlib import Path


def _bootstrap_nvidia_dll_paths() -> None:
    if not getattr(sys, "frozen", False):
        return

    candidates = []
    exe_dir = Path(sys.executable).resolve().parent
    internal_dir = Path(getattr(sys, "_MEIPASS", exe_dir))
    for base in (exe_dir / "nvidia", internal_dir / "nvidia"):
        if base.exists():
            candidates.extend(path for path in base.glob("*\\bin") if path.is_dir())

    for path in candidates:
        os.environ["PATH"] = f"{path}{os.pathsep}{os.environ.get('PATH', '')}"
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(path))


_bootstrap_nvidia_dll_paths()

if "--self-test-model" in sys.argv:
    from james_srt_studio.model_setup import default_model_dir
    from james_srt_studio.transcriber import load_best_model

    model, device = load_best_model(default_model_dir())
    result_path = Path(sys.executable).resolve().parent / "selftest_model.txt"
    result_path.write_text(f"model load ok {device}", encoding="utf-8")
    sys.exit(0)

if "--self-test-burmese" in sys.argv:
    from james_srt_studio.model_setup import default_burmese_asr_model_dir
    from james_srt_studio.transcriber import load_best_model

    model, device = load_best_model(default_burmese_asr_model_dir())
    result_path = Path(sys.executable).resolve().parent / "selftest_burmese.txt"
    result_path.write_text(f"burmese model load ok {device}", encoding="utf-8")
    sys.exit(0)

if "--self-test-assets" in sys.argv:
    from james_srt_studio.app import asset_path

    logo_png = asset_path("logo.png")
    logo_ico = asset_path("logo.ico")
    result_path = Path(sys.executable).resolve().parent / "selftest_assets.txt"
    result_path.write_text(
        f"logo_png={logo_png.is_file()} {logo_png}\n"
        f"logo_ico={logo_ico.is_file()} {logo_ico}",
        encoding="utf-8",
    )
    sys.exit(0)

if "--self-test-tts" in sys.argv:
    from james_srt_studio.pipeline import generate_tts_mp3_and_srt

    exe_dir = Path(sys.executable).resolve().parent
    out_dir = exe_dir / "selftest_tts"
    mp3_path, srt_path = generate_tts_mp3_and_srt(
        "မင်္ဂလာပါ။ နေကောင်းလား။",
        out_dir,
        base_name="selftest_myanmar_tts",
        language_code="my",
    )
    result_path = exe_dir / "selftest_tts.txt"
    result_path.write_text(
        f"mp3={mp3_path.is_file()} {mp3_path} {mp3_path.stat().st_size if mp3_path.is_file() else 0}\n"
        f"srt={srt_path.is_file()} {srt_path}",
        encoding="utf-8",
    )
    sys.exit(0)

from james_srt_studio.app import main


if __name__ == "__main__":
    main()
