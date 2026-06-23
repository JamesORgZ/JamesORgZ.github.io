from james_web_tool.models import edge_voice_options, emotion_options, gemini_voice_options, voice_display_options


def test_voice_options_include_sample_tool_v1_names():
    voices = voice_display_options()

    for label in [
        "စိုးကြီး (🇲🇲 - ကျား)",
        "စာဥ (🇲🇲 - မ)",
        "သခင်ကြီး (🇲🇲 - ကျား)",
        "ချောစု (🇲🇲 - မ)",
        "Chou Pro Lay (🇲🇲 - ကျား)",
        "ဂျိမ်း (🇺🇸 - ကျား)",
        "ဆိုဖီယာ (🇺🇸 - မ)",
        "မိုက်ကယ် (🇬🇧 - ကျား)",
        "ဂျနီဖာ (🇬🇧 - မ)",
    ]:
        assert label in voices


def test_voice_options_include_sample_tool_gemini_names():
    voices = gemini_voice_options()

    for label in [
        "Aoede (မ - လွတ်လပ်ပေါ့ပါး)",
        "Charon (ကျား - သတင်းကြေညာ)",
        "Puck (ကျား - မြူးကြွပျော်ရွှင်)",
        "Zubenelgenubi (ကျား - ထူးခြား)",
    ]:
        assert label in voices


def test_edge_voice_options_do_not_include_gemini_only_voices():
    voices = edge_voice_options()

    assert "အကိုလေး ( 🇲🇲 - ကျား)" in voices
    assert "Aoede (မ - လွတ်လပ်ပေါ့ပါး)" not in voices


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
