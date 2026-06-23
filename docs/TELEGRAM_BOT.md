# James Telegram Bot

This bot lets a buyer choose a plan in Telegram, sends the request to the admin,
and creates a 6-digit login PIN after admin approval.

## Plans

- 1 month VIP: 5000ks
- 3 months VIP: 12000ks
- 6 months VIP: 25000ks
- 1 year VIP: 35000ks
- Lifetime: 50000ks

## Run

Set these environment variables before starting the bot:

```powershell
$env:JAMES_TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
$env:JAMES_TELEGRAM_ADMIN_ID="5749918762"
python run_telegram_bot.py
```

Do not commit the real bot token. Keep it in your private environment or an
ignored `.env` file.

## PythonAnywhere webhook mode

For PythonAnywhere, use webhook mode instead of a long-running console task.
This avoids needing a paid Always-on task.

Required environment variables in the PythonAnywhere WSGI file:

```python
import os
os.environ["JAMES_TELEGRAM_BOT_TOKEN"] = "YOUR_BOT_TOKEN"
os.environ["JAMES_TELEGRAM_ADMIN_ID"] = "5749918762"
os.environ["JAMES_TELEGRAM_WEBHOOK_SECRET"] = "YOUR_PRIVATE_SECRET_PATH"
```

Set the WSGI file to import `pythonanywhere_wsgi.py`, then set the Telegram
webhook URL:

```powershell
$env:JAMES_TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
$env:JAMES_TELEGRAM_WEBHOOK_URL="https://Jamestts.pythonanywhere.com/telegram/YOUR_PRIVATE_SECRET_PATH"
python set_telegram_webhook.py
```

