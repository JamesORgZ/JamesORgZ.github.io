from james_srt_studio.text_aligner import align_text_to_duration, parse_srt_segments, split_original_text, strip_srt_to_text


def test_strip_srt_to_text_removes_numbers_and_timestamps():
    text = "1\n00:00:00,000 --> 00:00:01,000\nမင်္ဂလာပါ\n\n2\n00:00:01,000 --> 00:00:02,000\nနေကောင်းလား"
    assert strip_srt_to_text(text) == "မင်္ဂလာပါ\nနေကောင်းလား"


def test_split_original_text_prefers_burmese_phrase_endings():
    parts = split_original_text("သူ့ကိုကွာရှင်းဖို့မေ့လိုက်ပါဒီနေ့ဒီအိမ်ထဲကနေတောင်", max_chars=28)
    assert parts[0] == "သူ့ကိုကွာရှင်းဖို့မေ့လိုက်ပါ"


def test_align_text_to_duration_covers_full_duration():
    segments = align_text_to_duration("မင်္ဂလာပါ\nနေကောင်းလား", duration=10.0, max_chars=20)
    assert segments[0].start == 0
    assert segments[-1].end == 10.0
    assert [segment.text for segment in segments] == ["မင်္ဂလာပါ", "နေကောင်းလား"]


def test_parse_srt_segments_preserves_timestamps():
    text = "1\n00:00:00,140 --> 00:00:01,084\nသူ့ကိုကွာရှင်းဖို့မေ့လိုက်ပါ\n"
    segments = parse_srt_segments(text)
    assert segments[0].start == 0.14
    assert segments[0].end == 1.084
    assert segments[0].text == "သူ့ကိုကွာရှင်းဖို့မေ့လိုက်ပါ"
