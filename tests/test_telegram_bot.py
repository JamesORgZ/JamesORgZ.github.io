from james_web_tool.database import get_user_by_pin, init_db
from james_web_tool.models import PlanTier
from james_web_tool.telegram_bot import (
    PLAN_OPTIONS,
    create_pin_for_plan,
    create_webhook_application,
    generate_unique_pin,
    handle_callback,
    WEBSITE_URL,
)


class FakeApi:
    def __init__(self):
        self.sent_messages = []
        self.answered_callbacks = []

    def send_message(self, chat_id, text, reply_markup=None):
        self.sent_messages.append((chat_id, text, reply_markup))

    def answer_callback(self, callback_query_id, text):
        self.answered_callbacks.append((callback_query_id, text))


def call_wsgi(app, path, body=b"{}", method="POST"):
    result = {}

    def start_response(status, headers):
        result["status"] = status
        result["headers"] = headers

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": __import__("io").BytesIO(body),
        "HTTP_HOST": "Jamestts.pythonanywhere.com",
        "wsgi.url_scheme": "https",
    }
    result["body"] = b"".join(app(environ, start_response))
    return result


def test_plan_options_match_james_prices():
    assert PLAN_OPTIONS["1m"].price_label == "5000ks"
    assert PLAN_OPTIONS["3m"].price_label == "12000ks"
    assert PLAN_OPTIONS["6m"].price_label == "25000ks"
    assert PLAN_OPTIONS["1y"].price_label == "35000ks"
    assert PLAN_OPTIONS["life"].price_label == "50000ks"


def test_generate_unique_pin_skips_existing_pin(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)
    values = iter(["123456", "654321"])

    create_pin_for_plan(db_path, "1m", pin_factory=lambda: "123456")
    pin = generate_unique_pin(db_path, pin_factory=lambda: next(values))

    assert pin == "654321"


def test_create_pin_for_plan_creates_paid_user(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    init_db(db_path)

    user = create_pin_for_plan(db_path, "6m", pin_factory=lambda: "111222")

    assert user["pin"] == "111222"
    assert user["plan_tier"] == PlanTier.VIP.value
    assert user["expires_at"] is not None
    assert get_user_by_pin(db_path, "111222")["user_id"] == user["user_id"]


def test_webhook_application_processes_start_message(tmp_path):
    db_path = tmp_path / "app.sqlite3"
    fake_api = FakeApi()
    app = create_webhook_application(
        token="test-token",
        admin_id=5749918762,
        db_path=db_path,
        webhook_secret="secret-path",
        api_factory=lambda _token: fake_api,
    )
    body = b'{"message":{"chat":{"id":123},"text":"/start"}}'

    response = call_wsgi(app, "/telegram/secret-path", body)

    assert response["status"].startswith("200")
    assert fake_api.sent_messages[0][0] == 123
    assert "James Audio & SRT Generator" in fake_api.sent_messages[0][1]


def test_webhook_application_rejects_wrong_secret(tmp_path):
    fake_api = FakeApi()
    app = create_webhook_application(
        token="test-token",
        admin_id=5749918762,
        db_path=tmp_path / "app.sqlite3",
        webhook_secret="right-secret",
        api_factory=lambda _token: fake_api,
    )

    response = call_wsgi(app, "/telegram/wrong-secret", b'{"message":{"chat":{"id":123},"text":"/start"}}')

    assert response["status"].startswith("404")
    assert fake_api.sent_messages == []


def test_webhook_application_can_set_webhook_from_secret_setup_path(tmp_path):
    calls = []
    app = create_webhook_application(
        token="test-token",
        admin_id=5749918762,
        db_path=tmp_path / "app.sqlite3",
        webhook_secret="right-secret",
        api_factory=lambda _token: FakeApi(),
        webhook_setter=lambda token, url: calls.append((token, url)) or {"ok": True},
    )

    response = call_wsgi(app, "/telegram/right-secret/setup-webhook", method="GET")

    assert response["status"].startswith("200")
    assert calls == [("test-token", "https://Jamestts.pythonanywhere.com/telegram/right-secret")]


def test_buy_plan_shows_kpay_copy_box_before_admin_request(tmp_path):
    fake_api = FakeApi()
    callback = {
        "id": "cb1",
        "data": "buy:1m",
        "from": {"id": 2037708908, "username": "buyer"},
        "message": {"chat": {"id": 2037708908}},
    }

    handle_callback(fake_api, tmp_path / "app.sqlite3", 5749918762, callback)

    assert len(fake_api.sent_messages) == 1
    chat_id, text, reply_markup = fake_api.sent_messages[0]
    assert chat_id == 2037708908
    assert "KPay" in text
    assert "09691505900" in text
    assert "Aung Pyae Phyoe" in text
    assert reply_markup["inline_keyboard"][0][0]["copy_text"]["text"] == "09691505900"
    flat_buttons = [button for row in reply_markup["inline_keyboard"] for button in row]
    assert any(button.get("url") == "https://t.me/JamesOrg" for button in flat_buttons)
    assert any(button.get("callback_data") == "paid:1m" for button in flat_buttons)
    assert "ငွေလွှဲ" in text
    assert all("ငွေလွဲ" not in button["text"] for button in flat_buttons)


def test_payment_done_sends_purchase_request_to_admin(tmp_path):
    fake_api = FakeApi()
    callback = {
        "id": "cb2",
        "data": "paid:3m",
        "from": {"id": 2037708908, "username": "buyer"},
        "message": {"chat": {"id": 2037708908}},
    }

    handle_callback(fake_api, tmp_path / "app.sqlite3", 5749918762, callback)

    assert fake_api.sent_messages[0][0] == 5749918762
    assert "New purchase request" in fake_api.sent_messages[0][1]
    assert "3 Months VIP" in fake_api.sent_messages[0][1]
    assert fake_api.sent_messages[1][0] == 2037708908


def test_longer_plans_are_vip():
    assert PLAN_OPTIONS["6m"].label == "6 Months VIP"
    assert PLAN_OPTIONS["1y"].label == "1 Year VIP"
    assert PLAN_OPTIONS["6m"].grant.tier == PlanTier.VIP
    assert PLAN_OPTIONS["1y"].grant.tier == PlanTier.VIP


def test_admin_approve_sends_active_pin_and_website_link(tmp_path):
    fake_api = FakeApi()
    callback = {
        "id": "cb3",
        "data": "approve:1m:2037708908",
        "from": {"id": 5749918762, "username": "JamesOrg"},
        "message": {"chat": {"id": 5749918762}},
    }

    handle_callback(fake_api, tmp_path / "app.sqlite3", 5749918762, callback)

    user_message = fake_api.sent_messages[0][1]
    assert "Payment approved" in user_message
    assert "Login PIN:" in user_message
    assert WEBSITE_URL in user_message
    assert "active" in user_message.lower()
