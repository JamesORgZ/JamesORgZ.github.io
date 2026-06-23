from james_srt_studio.timecode import format_srt_timestamp


def test_zero_timestamp():
    assert format_srt_timestamp(0) == "00:00:00,000"


def test_timestamp_with_hours_minutes_seconds_and_milliseconds():
    assert format_srt_timestamp(3723.456) == "01:02:03,456"


def test_timestamp_rounds_to_nearest_millisecond():
    assert format_srt_timestamp(1.9996) == "00:00:02,000"


def test_negative_timestamp_clamps_to_zero():
    assert format_srt_timestamp(-2.5) == "00:00:00,000"
