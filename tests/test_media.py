from pathlib import Path

from james_srt_studio.media import build_ffmpeg_command, is_supported_media


def test_supported_media_extensions():
    assert is_supported_media(Path("voice.mp3"))
    assert is_supported_media(Path("movie.mp4"))
    assert not is_supported_media(Path("notes.txt"))


def test_build_ffmpeg_command_normalizes_to_16khz_mono_wav():
    cmd = build_ffmpeg_command(Path("input.mp4"), Path("work.wav"))
    assert cmd == [
        "ffmpeg",
        "-y",
        "-i",
        "input.mp4",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-acodec",
        "pcm_s16le",
        "work.wav",
    ]
