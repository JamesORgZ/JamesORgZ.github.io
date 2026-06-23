from pathlib import Path

from james_srt_studio.pipeline import output_srt_path


def test_output_srt_path_replaces_extension():
    assert output_srt_path(Path(r"C:\Audio\voice.mp3")) == Path(r"C:\Audio\voice.srt")
