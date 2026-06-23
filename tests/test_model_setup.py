from pathlib import Path

from james_srt_studio.model_setup import default_model_dir, model_exists


def test_default_model_dir_uses_base_dir():
    assert default_model_dir(Path("C:/Tool")) == Path("C:/Tool/models/faster-whisper-large-v3")


def test_default_burmese_model_dir_uses_base_dir():
    from james_srt_studio.model_setup import default_burmese_asr_model_dir

    assert default_burmese_asr_model_dir(Path("C:/Tool")) == Path("C:/Tool/models/faster-whisper-small-burmese-v3")


def test_model_exists_requires_files(tmp_path):
    model_dir = tmp_path / "model"
    assert not model_exists(model_dir)
    model_dir.mkdir()
    assert not model_exists(model_dir)
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    assert model_exists(model_dir)
