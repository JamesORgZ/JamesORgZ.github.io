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
