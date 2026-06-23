from __future__ import annotations

import os
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

os.environ.setdefault("JAMES_WEB_DATA_DIR", str(Path(__file__).resolve().parent / "web_data"))

from james_web_tool.ui import build_app, launch_kwargs_from_env


demo = build_app().queue(api_open=False)


if __name__ == "__main__":
    launch_kwargs = launch_kwargs_from_env()
    if os.getenv("SPACE_ID"):
        launch_kwargs["share"] = True
    demo.launch(**launch_kwargs)
