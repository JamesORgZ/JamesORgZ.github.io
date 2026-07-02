from __future__ import annotations

import base64
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.request
import wave

from james_srt_studio.text_aligner import media_duration_seconds
from james_srt_studio.tts_generator import synthesize_and_measure

from .models import edge_voice_options, elevenlabs_voice_options, gemini_voice_options, voice_display_options

GEMINI_MODEL_IDS = {
    "Gemini 3.1 Flash": "gemini-3.1-flash-tts-preview",
    "Gemini 2.5 Flash": "gemini-2.5-flash-preview-tts",
}


def voice_id_for_label(label: str) -> str:
    voices = voice_display_options()
    if label not in voices:
        return voices["မြန်မာမ ၂"]
    return voices[label]


def edge_voice_id_for_label(label: str) -> str:
    voices = edge_voice_options()
    if label not in voices:
        return voices["မြန်မာမ ၂"]
    return voices[label]


def gemini_voice_id_for_label(label: str) -> str:
    voices = gemini_voice_options()
    if label not in voices:
        return voices["ကြယ်နု ၁"]
    return voices[label]


def elevenlabs_voice_id_for_label(label: str) -> str:
    voices = elevenlabs_voice_options()
    if label not in voices:
        return voices["အေးချမ်းမ ၁"]
    return voices[label]


def gemini_model_id_for_label(label: str) -> str:
    return GEMINI_MODEL_IDS.get(label, GEMINI_MODEL_IDS["Gemini 3.1 Flash"])


def generate_mp3(text: str, mp3_path: Path, voice_id: str, rate: str = "+0%") -> float:
    _path, duration = synthesize_and_measure(text=text, out_mp3=mp3_path, voice=voice_id, rate=rate)
    return duration


def emotion_prompt(text: str, emotion: str) -> str:
    style_map = {
        "Movie Recap (ဇာတ်လမ်းပြော)": "Say this in a dramatic movie recap narrator style",
        "Storytelling (ပုံပြင်ပြော)": "Say this like warm storytelling",
        "Excited (စိတ်လှုပ်ရှား)": "Say this excitedly",
        "Sad (ဝမ်းနည်း)": "Say this sadly",
        "Angry (ဒေါသထွက်)": "Say this angrily",
        "Serious/News (သတင်းကြေညာ/တည်ငြိမ်)": "Say this in a serious news announcer style",
        "Suspense/Thriller (သည်းထိတ်ရင်ဖို)": "Say this with suspense and thriller tension",
        "Romantic/Soft (ချစ်စရာ/နူးညံ့)": "Say this softly and romantically",
        "Sarcastic/Funny (ဟာသ/နောက်ပြောင်)": "Say this sarcastically and playfully",
        "Documentary (မှတ်တမ်းရုပ်ရှင်)": "Say this in a calm documentary narrator style",
    }
    instruction = style_map.get(emotion, "Say this clearly")
    return f"{instruction}, preserving the original language exactly:\n{text}"


def _write_wav(filename: Path, pcm: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> None:
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def _convert_wav_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    completed = subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-q:a", "2", str(mp3_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Could not convert Gemini audio to MP3.")


def generate_gemini_mp3(
    text: str,
    mp3_path: Path,
    voice_id: str,
    model_id: str,
    api_key: str,
    emotion: str,
) -> float:
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "model": model_id,
        "input": emotion_prompt(text, emotion),
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice_id}]},
    }
    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
            "Api-Revision": "2026-05-20",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini TTS request failed: {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gemini TTS request failed: {exc.reason}") from exc

    audio_data = payload.get("output_audio", {}).get("data")
    if not audio_data:
        raise RuntimeError("Gemini TTS response did not include audio data.")

    wav_path = mp3_path.with_suffix(".gemini.wav")
    _write_wav(wav_path, base64.b64decode(audio_data))
    _convert_wav_to_mp3(wav_path, mp3_path)
    wav_path.unlink(missing_ok=True)
    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        raise RuntimeError("Gemini TTS failed to create MP3 output.")
    return media_duration_seconds(mp3_path)


def generate_elevenlabs_mp3(
    text: str,
    mp3_path: Path,
    voice_id: str,
    api_key: str,
    emotion: str,
    model_id: str = "eleven_multilingual_v2",
) -> float:
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "text": emotion_prompt(text, emotion),
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.75,
            "style": 0.25,
            "use_speaker_boost": True,
        },
    }
    request = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            audio = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"ElevenLabs TTS request failed: {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ElevenLabs TTS request failed: {exc.reason}") from exc

    mp3_path.write_bytes(audio)
    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        raise RuntimeError("ElevenLabs TTS failed to create MP3 output.")
    return media_duration_seconds(mp3_path)


