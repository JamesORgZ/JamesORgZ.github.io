from james_web_tool.ui import launch_kwargs_from_env


def test_launch_kwargs_use_render_port(monkeypatch):
    monkeypatch.setenv("PORT", "10000")

    assert launch_kwargs_from_env() == {"server_name": "0.0.0.0", "server_port": 10000}


def test_launch_kwargs_default_to_gradio_local_port(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)

    assert launch_kwargs_from_env() == {"server_name": "0.0.0.0", "server_port": 7860}


def test_render_app_exposes_gradio_and_telegram_webhook():
    import app as render_app

    paths = {getattr(route, "path", "") for route in render_app.app.routes}

    assert render_app.demo.__class__.__name__ == "Blocks"
    assert "/telegram/{webhook_secret}" in paths
    assert "/telegram/{webhook_secret}/setup-webhook" in paths
