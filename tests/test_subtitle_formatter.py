from james_srt_studio.subtitle_formatter import (
    SubtitleSegment,
    build_srt,
    wrap_subtitle_text,
)


def test_burmese_phrase_split_matches_user_example():
    text = "မောင်မောင်ကနေမကောင်းလို့အပြင်မသွားဘူး"
    assert wrap_subtitle_text(text, max_chars=25) == [
        "မောင်မောင်ကနေမကောင်းလို့",
        "အပြင်မသွားဘူး",
    ]


def test_burmese_combining_marks_stay_attached():
    text = "မောင်မောင်ကနေမကောင်းလို့အပြင်မသွားဘူး"
    lines = wrap_subtitle_text(text, max_chars=12)
    assert "".join(lines) == text
    for line in lines:
        assert not line.startswith(
            ("ါ", "ာ", "ိ", "ီ", "ု", "ူ", "ေ", "ဲ", "ံ", "့", "း", "်", "ျ", "ြ", "ွ", "ှ")
        )


def test_english_wraps_on_spaces():
    assert wrap_subtitle_text("James goes to the cinema today", max_chars=12) == [
        "James goes",
        "to the",
        "cinema today",
    ]


def test_build_srt_uses_standard_timestamp_and_wrapped_text():
    srt = build_srt(
        [
            SubtitleSegment(0, 3.5, "မောင်မောင်ကနေမကောင်းလို့အပြင်မသွားဘူး"),
        ],
        max_chars=25,
    )
    assert srt == (
        "1\n"
        "00:00:00,000 --> 00:00:03,500\n"
        "မောင်မောင်ကနေမကောင်းလို့\n"
        "အပြင်မသွားဘူး\n"
    )
