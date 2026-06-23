from __future__ import annotations

import json
import os
import random
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

from .admin import create_paid_user
from .config import default_db_path
from .database import get_user_by_pin, init_db
from .models import PlanGrant


@dataclass(frozen=True)
class PlanOption:
    key: str
    label: str
    price_label: str
    grant: PlanGrant


PLAN_OPTIONS = {
    "1m": PlanOption("1m", "1 Month VIP", "5000ks", PlanGrant.ONE_MONTH),
    "3m": PlanOption("3m", "3 Months VIP", "12000ks", PlanGrant.THREE_MONTHS),
    "6m": PlanOption("6m", "6 Months VIP", "25000ks", PlanGrant.SIX_MONTHS),
    "1y": PlanOption("1y", "1 Year VIP", "35000ks", PlanGrant.ONE_YEAR),
    "life": PlanOption("life", "Lifetime", "50000ks", PlanGrant.LIFETIME),
}

KPAY_PHONE = "09691505900"
KPAY_NAME = "Aung Pyae Phyoe"
ADMIN_TELEGRAM_URL = "https://t.me/JamesOrg"
WEBSITE_URL = os.getenv("JAMES_WEBSITE_URL", "https://jamesorgggh-james-audio-srt-generator.hf.space")


def default_pin_factory() -> str:
    return f"{random.SystemRandom().randint(0, 999999):06d}"


def generate_unique_pin(db_path: Path, pin_factory: Callable[[], str] = default_pin_factory) -> str:
    for _ in range(100):
        pin = pin_factory()
        if len(pin) == 6 and pin.isdigit() and get_user_by_pin(db_path, pin) is None:
            return pin
    raise RuntimeError("Could not generate a unique 6-digit PIN.")


def create_pin_for_plan(
    db_path: Path,
    plan_key: str,
    pin_factory: Callable[[], str] = default_pin_factory,
) -> dict[str, Any]:
    if plan_key not in PLAN_OPTIONS:
        raise ValueError(f"Unknown plan: {plan_key}")
    init_db(db_path)
    pin = generate_unique_pin(db_path, pin_factory=pin_factory)
    return create_paid_user(db_path, pin=pin, grant=PLAN_OPTIONS[plan_key].grant)


def plan_keyboard() -> dict[str, Any]:
    rows = []
    for option in PLAN_OPTIONS.values():
        rows.append(
            [
                {
                    "text": f"{option.label} - {option.price_label}",
                    "callback_data": f"buy:{option.key}",
                }
            ]
        )
    return {"inline_keyboard": rows}


def admin_approval_keyboard(plan_key: str, user_chat_id: int) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Approve", "callback_data": f"approve:{plan_key}:{user_chat_id}"},
                {"text": "❌ Reject", "callback_data": f"reject:{plan_key}:{user_chat_id}"},
            ]
        ]
    }


def payment_keyboard(plan_key: str) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "📋 Copy KPay Number",
                    "copy_text": {"text": KPAY_PHONE},
                }
            ],
            [
                {"text": "💬 Admin ကိုသွားမယ်", "url": ADMIN_TELEGRAM_URL},
            ],
            [
                {"text": "✅ ငွေလွှဲပြီးပြီ / Admin ကိုအကြောင်းကြားမယ်", "callback_data": f"paid:{plan_key}"},
            ],
        ]
    }


def payment_text(option: PlanOption) -> str:
    return (
        f"💳 {option.label} ဝယ်ယူရန်\n"
        f"Price: {option.price_label}\n\n"
        "KPay နဲ့ငွေလွှဲပါ:\n"
        f"Phone: `{KPAY_PHONE}`\n"
        f"Name: {KPAY_NAME}\n\n"
        "ဖုန်းနံပါတ်ကို copy လုပ်ပြီး ငွေလွှဲပါ။\n"
        "ငွေလွှဲပြီးရင် အောက်က ✅ ခလုတ်နှိပ်ပါ။"
    )


def send_purchase_request(api: TelegramApi, admin_id: int, plan_key: str, chat_id: int, from_user: dict[str, Any]) -> None:
    option = PLAN_OPTIONS[plan_key]
    username = f"@{from_user['username']}" if from_user.get("username") else from_user.get("first_name", "User")
    api.send_message(
        admin_id,
        (
            "🧾 New purchase request\n\n"
            f"User: {username}\n"
            f"Telegram ID: {chat_id}\n"
            f"Plan: {option.label}\n"
            f"Price: {option.price_label}\n"
            f"KPay: {KPAY_PHONE}\n"
            f"Name: {KPAY_NAME}\n\n"
            "Payment စစ်ပြီး approve နှိပ်ပါ။"
        ),
        reply_markup=admin_approval_keyboard(plan_key, chat_id),
    )


class TelegramApi:
    def __init__(self, token: str):
        self.base_url = f"https://api.telegram.org/bot{token}"

    def call(self, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = urllib.parse.urlencode(payload or {}).encode("utf-8")
        request = urllib.request.Request(f"{self.base_url}/{method}", data=data, method="POST")
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not result.get("ok"):
            raise RuntimeError(result)
        return result

    def send_message(self, chat_id: int | str, text: str, reply_markup: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_markup is not None:
            payload["reply_markup"] = json.dumps(reply_markup)
        self.call("sendMessage", payload)

    def answer_callback(self, callback_query_id: str, text: str) -> None:
        self.call("answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text})

    def get_updates(self, offset: int | None = None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": 45}
        if offset is not None:
            payload["offset"] = offset
        return self.call("getUpdates", payload)["result"]


def start_text() -> str:
    return (
        "🎙 James Audio & SRT Generator\n\n"
        "Plan ဝယ်ချင်ရင် အောက်က plan ကိုရွေးပါ။\n"
        "Admin confirm ပြီးတာနဲ့ 6-digit login PIN ပို့ပေးမယ်။"
    )


def handle_message(api: TelegramApi, message: dict[str, Any]) -> None:
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    if text.startswith("/start"):
        api.send_message(chat_id, start_text(), reply_markup=plan_keyboard())


def handle_callback(api: TelegramApi, db_path: Path, admin_id: int, callback: dict[str, Any]) -> None:
    callback_id = callback["id"]
    data = callback.get("data", "")
    from_user = callback["from"]
    chat_id = callback["message"]["chat"]["id"]

    if data.startswith("buy:"):
        plan_key = data.split(":", 1)[1]
        option = PLAN_OPTIONS[plan_key]
        api.send_message(chat_id, payment_text(option), reply_markup=payment_keyboard(plan_key))
        api.answer_callback(callback_id, "KPay အချက်အလက်ပို့ပြီးပါပြီ။")
        return

    if data.startswith("paid:"):
        plan_key = data.split(":", 1)[1]
        send_purchase_request(api, admin_id, plan_key, chat_id, from_user)
        api.answer_callback(callback_id, "Admin ဆီ request ပို့ပြီးပါပြီ။")
        api.send_message(chat_id, "✅ Request ပို့ပြီးပါပြီ။ Admin က payment စစ်ပြီး approve လုပ်ပေးပါမယ်။")
        return

    if data.startswith("approve:"):
        if from_user["id"] != admin_id:
            api.answer_callback(callback_id, "Admin only.")
            return
        _, plan_key, user_chat_id = data.split(":", 2)
        user = create_pin_for_plan(db_path, plan_key)
        option = PLAN_OPTIONS[plan_key]
        api.send_message(
            user_chat_id,
            (
                "✅ Payment approved!\n\n"
                f"Plan: {option.label}\n"
                f"Login PIN: {user['pin']}\n"
                "Status: active\n"
                f"Website: {WEBSITE_URL}\n\n"
                "ဒီ PIN နဲ့ website မှာ Login ဝင်ပြီးအသုံးပြုပါ။"
            ),
        )
        api.answer_callback(callback_id, f"Created PIN {user['pin']}")
        return

    if data.startswith("reject:"):
        if from_user["id"] != admin_id:
            api.answer_callback(callback_id, "Admin only.")
            return
        _, _plan_key, user_chat_id = data.split(":", 2)
        api.send_message(user_chat_id, "❌ Request rejected. Admin ကိုပြန်ဆက်သွယ်ပါ။")
        api.answer_callback(callback_id, "Rejected.")


def process_update(api: TelegramApi, db_path: Path, admin_id: int, update: dict[str, Any]) -> None:
    if "message" in update:
        handle_message(api, update["message"])
    if "callback_query" in update:
        handle_callback(api, db_path, admin_id, update["callback_query"])


def create_webhook_application(
    token: str,
    admin_id: int,
    db_path: Path | None = None,
    webhook_secret: str | None = None,
    api_factory: Callable[[str], TelegramApi] = TelegramApi,
    webhook_setter: Callable[[str, str], dict[str, Any]] | None = None,
):
    active_db_path = db_path or default_db_path()
    init_db(active_db_path)
    api = api_factory(token)
    expected_path = f"/telegram/{webhook_secret}" if webhook_secret else "/telegram"
    setup_path = f"{expected_path}/setup-webhook"

    def application(environ, start_response):
        method = environ.get("REQUEST_METHOD")
        path = environ.get("PATH_INFO")

        if method == "GET" and path == setup_path:
            scheme = environ.get("wsgi.url_scheme", "https")
            host = environ.get("HTTP_HOST", "")
            webhook_url = f"{scheme}://{host}{expected_path}"
            setter = webhook_setter or set_webhook
            result = setter(token, webhook_url)
            status = "200 OK" if result.get("ok") else "500 Internal Server Error"
            start_response(status, [("Content-Type", "application/json; charset=utf-8")])
            return [json.dumps({"ok": result.get("ok"), "url": webhook_url}).encode("utf-8")]

        if method != "POST" or path != expected_path:
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"not found"]

        try:
            content_length = int(environ.get("CONTENT_LENGTH") or "0")
            body = environ["wsgi.input"].read(content_length)
            update = json.loads(body.decode("utf-8") or "{}")
            process_update(api, active_db_path, admin_id, update)
            start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"ok"]
        except Exception as exc:
            print(f"Telegram webhook error: {exc}")
            start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"error logged"]

    return application


def create_webhook_application_from_env():
    token = os.getenv("JAMES_TELEGRAM_BOT_TOKEN", "").strip()
    admin_id = os.getenv("JAMES_TELEGRAM_ADMIN_ID", "").strip()
    webhook_secret = os.getenv("JAMES_TELEGRAM_WEBHOOK_SECRET", "").strip()
    if not token:
        raise RuntimeError("JAMES_TELEGRAM_BOT_TOKEN is required.")
    if not admin_id.isdigit():
        raise RuntimeError("JAMES_TELEGRAM_ADMIN_ID must be a number.")
    if not webhook_secret:
        raise RuntimeError("JAMES_TELEGRAM_WEBHOOK_SECRET is required.")
    return create_webhook_application(token=token, admin_id=int(admin_id), webhook_secret=webhook_secret)


def set_webhook(token: str, webhook_url: str) -> dict[str, Any]:
    return TelegramApi(token).call("setWebhook", {"url": webhook_url})


def set_webhook_from_env() -> dict[str, Any]:
    token = os.getenv("JAMES_TELEGRAM_BOT_TOKEN", "").strip()
    webhook_url = os.getenv("JAMES_TELEGRAM_WEBHOOK_URL", "").strip()
    if not token:
        raise RuntimeError("JAMES_TELEGRAM_BOT_TOKEN is required.")
    if not webhook_url:
        raise RuntimeError("JAMES_TELEGRAM_WEBHOOK_URL is required.")
    return set_webhook(token, webhook_url)


def run_bot(token: str, admin_id: int, db_path: Path | None = None) -> None:
    active_db_path = db_path or default_db_path()
    init_db(active_db_path)
    api = TelegramApi(token)
    offset: int | None = None
    while True:
        try:
            for update in api.get_updates(offset=offset):
                offset = update["update_id"] + 1
                process_update(api, active_db_path, admin_id, update)
        except Exception as exc:
            print(f"Telegram bot error: {exc}")
            time.sleep(5)


def run_from_env() -> None:
    token = os.getenv("JAMES_TELEGRAM_BOT_TOKEN", "").strip()
    admin_id = os.getenv("JAMES_TELEGRAM_ADMIN_ID", "").strip()
    if not token:
        raise RuntimeError("JAMES_TELEGRAM_BOT_TOKEN is required.")
    if not admin_id.isdigit():
        raise RuntimeError("JAMES_TELEGRAM_ADMIN_ID must be a number.")
    run_bot(token=token, admin_id=int(admin_id))
