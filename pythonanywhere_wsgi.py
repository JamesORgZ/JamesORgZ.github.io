import os
import sys
from pathlib import Path


project_root = Path(__file__).resolve().parent
src_path = project_root / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        key, value = clean.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(project_root / ".env")
os.environ.setdefault("JAMES_WEB_DATA_DIR", str(project_root / "web_data"))

from james_web_tool.telegram_bot import create_webhook_application_from_env


application = create_webhook_application_from_env()
