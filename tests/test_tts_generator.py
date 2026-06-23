from james_srt_studio.tts_generator import voice_for_language


def test_voice_for_burmese():
    assert voice_for_language("my") == "my-MM-NilarNeural"


def test_voice_for_english():
    assert voice_for_language("en") == "en-US-JennyNeural"
