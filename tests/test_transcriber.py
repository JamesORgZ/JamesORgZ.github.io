from types import SimpleNamespace

from james_srt_studio.transcriber import whisper_segments_to_subtitle_segments


def test_whisper_segments_convert_to_subtitle_segments():
    whisper_segments = [
        SimpleNamespace(start=0.0, end=1.25, text=" Hello "),
        SimpleNamespace(start=1.25, end=2.5, text="မင်္ဂလာပါ"),
    ]
    result = whisper_segments_to_subtitle_segments(whisper_segments)
    assert [(s.start, s.end, s.text) for s in result] == [
        (0.0, 1.25, "Hello"),
        (1.25, 2.5, "မင်္ဂလာပါ"),
    ]
