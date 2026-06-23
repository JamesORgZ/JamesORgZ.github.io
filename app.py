from __future__ import annotations

import os
import sys
from pathlib import Path

import gradio as gr
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from james_web_tool.config import default_db_path
from james_web_tool.database import init_db
from james_web_tool.telegram_bot import TelegramApi, process_update, set_webhook
from james_web_tool.ui import build_app


fastapi_app = FastAPI()
os.environ.setdefault("JAMES_WEB_DATA_DIR", str(Path(__file__).resolve().parent / "web_data"))
demo = build_app().queue()


def telegram_env() -> tuple[str, int, str]:
    token = os.getenv("JAMES_TELEGRAM_BOT_TOKEN", "").strip()
    admin_id = os.getenv("JAMES_TELEGRAM_ADMIN_ID", "").strip()
    secret = os.getenv("JAMES_TELEGRAM_WEBHOOK_SECRET", "").strip()
    if not token or not admin_id.isdigit() or not secret:
        raise HTTPException(status_code=503, detail="Telegram bot environment is not configured.")
    return token, int(admin_id), secret


@fastapi_app.post("/telegram/{webhook_secret}")
async def telegram_webhook(webhook_secret: str, request: Request):
    token, admin_id, expected_secret = telegram_env()
    if webhook_secret != expected_secret:
        raise HTTPException(status_code=404, detail="Not found")

    db_path = default_db_path()
    init_db(db_path)
    update = await request.json()
    process_update(TelegramApi(token), db_path, admin_id, update)
    return JSONResponse({"ok": True})


@fastapi_app.get("/telegram/{webhook_secret}/setup-webhook")
async def setup_telegram_webhook(webhook_secret: str, request: Request):
    token, _admin_id, expected_secret = telegram_env()
    if webhook_secret != expected_secret:
        raise HTTPException(status_code=404, detail="Not found")

    webhook_url = str(request.url_for("telegram_webhook", webhook_secret=webhook_secret))
    result = set_webhook(token, webhook_url)
    return JSONResponse({"ok": result.get("ok"), "url": webhook_url})


app = gr.mount_gradio_app(fastapi_app, demo, path="/")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "7860")))
