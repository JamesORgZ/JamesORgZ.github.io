---
title: James Audio SRT Generator
emoji: 🎙️
colorFrom: purple
colorTo: yellow
sdk: gradio
sdk_version: 6.19.0
python_version: "3.11"
app_file: app.py
pinned: false
---

# James Audio & SRT Generator

Public Gradio web tool for James Audio & SRT Generator.

## Web features

- Free marketing tool
- PIN login for VIP/VVIP users
- Admin panel
- Myanmar/English TTS + MP3/SRT export

## Runtime

The app starts from `app.py`.

Required secrets for Telegram webhook:

- `JAMES_TELEGRAM_BOT_TOKEN`
- `JAMES_TELEGRAM_ADMIN_ID`
- `JAMES_TELEGRAM_WEBHOOK_SECRET`

---

# James SRT Studio

Windows desktop tool for converting audio/video files into `.srt` subtitle files.

Core behavior:

- Transcribes original spoken language; it does not translate.
- Uses local faster-whisper large-v3 after setup.
- Outputs standard SRT timestamps like `00:00:00,000`.
- Wraps Burmese lines safely at a maximum of 25 characters.

## Run

```powershell
python -m pip install -e .[dev]
python -m james_srt_studio.app
```

The first real transcription downloads the local Whisper model if it is not installed yet. After that, the app can run without internet.
