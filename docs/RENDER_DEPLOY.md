# Render deploy

This project can run as a Render Web Service.

## Settings

- Build command: `pip install -r requirements.txt`
- Start command: `python app.py`
- Environment:
  - `JAMES_WEB_DATA_DIR=/opt/render/project/src/web_data`
  - `GRADIO_SERVER_NAME=0.0.0.0`
  - `JAMES_TELEGRAM_ADMIN_ID=5749918762`
  - `JAMES_TELEGRAM_WEBHOOK_SECRET=james-telegram-webhook-5749918762`
  - `JAMES_TELEGRAM_BOT_TOKEN=<your bot token>`

Render provides `PORT` automatically. The app reads it at startup.

The Render service hosts both:

- the customer Gradio website at `/`
- the Telegram webhook at `/telegram/<JAMES_TELEGRAM_WEBHOOK_SECRET>`

This keeps Telegram-created PINs and website logins on the same SQLite database.

## Notes

- `http://127.0.0.1:7860/` is local only and is not a customer URL.
- Render will provide a public URL like `https://your-service.onrender.com`.
- Free Render services can sleep when inactive. Paid instances avoid cold starts.
