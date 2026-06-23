from james_web_tool.models import edge_voice_options, emotion_options, gemini_voice_options, voice_display_options


def test_voice_options_include_sample_tool_v1_names():
    voices = voice_display_options()

    for label in [
        "James Hero MM-01 (Male)",
        "James Velvet MM-02 (Female)",
        "James Cinema MM-03 (Male)",
        "James Pearl MM-04 (Female)",
        "James Pulse US-01 (Male)",
        "James Luna US-02 (Female)",
        "James Royal UK-01 (Male)",
        "James Rose UK-02 (Female)",
    ]:
        assert label in voices


def test_voice_options_include_sample_tool_gemini_names():
    voices = gemini_voice_options()

    for label in [
        "James Nova G-01 (Female)",
        "James Anchor G-06 (Male)",
        "James Spark G-10 (Male)",
        "James Titan G-30 (Male)",
    ]:
        assert label in voices


def test_edge_voice_options_do_not_include_gemini_only_voices():
    voices = edge_voice_options()

    assert "James Hero MM-01 (Male)" in voices
    assert "James Nova G-01 (Female)" not in voices


def test_old_sample_tool_voice_names_are_not_displayed():
    voices = voice_display_options()

    for old_label in [
        "မြမြ",
        "အကိုလေး",
        "နီလာ",
        "သီဟ",
        "အကိုလေး ( 🇲🇲 - ကျား)",
        "စိုးကြီး (🇲🇲 - ကျား)",
        "Aoede (မ - လွတ်လပ်ပေါ့ပါး)",
        "Charon (ကျား - သတင်းကြေညာ)",
        "Puck (ကျား - မြူးကြွပျော်ရွှင်)",
    ]:
        assert old_label not in voices


def test_emotion_options_include_sample_tool_styles():
    emotions = emotion_options()

    assert emotions == [
        "Movie Recap (ဇာတ်လမ်းပြော)",
        "Storytelling (ပုံပြင်ပြော)",
        "Excited (စိတ်လှုပ်ရှား)",
        "Sad (ဝမ်းနည်း)",
        "Angry (ဒေါသထွက်)",
        "Serious/News (သတင်းကြေညာ/တည်ငြိမ်)",
        "Suspense/Thriller (သည်းထိတ်ရင်ဖို)",
        "Romantic/Soft (ချစ်စရာ/နူးညံ့)",
        "Sarcastic/Funny (ဟာသ/နောက်ပြောင်)",
        "Documentary (မှတ်တမ်းရုပ်ရှင်)",
    ]
