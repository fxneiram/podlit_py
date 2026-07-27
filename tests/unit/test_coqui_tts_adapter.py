import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adapters.driven.tts.coqui_tts_adapter import CoquiTTSAdapter
from domain.exceptions import SSMLNotSupportedError, VoiceNotFoundError


@pytest.fixture
def mock_tts_class():
    with patch("adapters.driven.tts.coqui_tts_adapter.TTS") as mock_class:
        mock_instance = MagicMock()
        mock_instance.to.return_value = mock_instance
        mock_class.return_value = mock_instance
        yield mock_class


@pytest.fixture
def no_cuda():
    with patch("adapters.driven.tts.coqui_tts_adapter.torch.cuda.is_available", return_value=False):
        yield


@pytest.fixture
def cuda_available():
    with patch("adapters.driven.tts.coqui_tts_adapter.torch.cuda.is_available", return_value=True):
        yield


def test_selects_cpu_device_when_cuda_unavailable(mock_tts_class, no_cuda):
    CoquiTTSAdapter()

    mock_tts_class.return_value.to.assert_called_once_with("cpu")


def test_selects_cuda_device_when_available(mock_tts_class, cuda_available):
    CoquiTTSAdapter()

    mock_tts_class.return_value.to.assert_called_once_with("cuda")


@pytest.fixture
def voices_dir(tmp_path):
    (tmp_path / "narrator.wav").write_bytes(b"")
    return str(tmp_path)


def test_synthesize_resolves_voice_to_sample_voices_path(mock_tts_class, no_cuda, voices_dir):
    adapter = CoquiTTSAdapter(voices_dir=voices_dir)

    adapter.synthesize(
        content="Hello world",
        language="en",
        voice="narrator.wav",
        speed=1.2,
        output_path="out.wav",
    )

    mock_tts_class.return_value.tts_to_file.assert_called_once_with(
        text="Hello world",
        speaker_wav=f"{voices_dir}/narrator.wav",
        language="en",
        file_path="out.wav",
        speed=1.2,
    )


def test_synthesize_raises_when_ssml_requested(mock_tts_class, no_cuda, voices_dir):
    adapter = CoquiTTSAdapter(voices_dir=voices_dir)

    with pytest.raises(SSMLNotSupportedError):
        adapter.synthesize(
            content="<speak>Hello</speak>",
            language="en",
            voice="narrator.wav",
            speed=1.0,
            output_path="out.wav",
            is_ssml=True,
        )

    mock_tts_class.return_value.tts_to_file.assert_not_called()


def test_synthesize_raises_when_voice_not_found(mock_tts_class, no_cuda, voices_dir):
    adapter = CoquiTTSAdapter(voices_dir=voices_dir)

    with pytest.raises(VoiceNotFoundError):
        adapter.synthesize(
            content="Hello world",
            language="en",
            voice="missing.wav",
            speed=1.0,
            output_path="out.wav",
        )

    mock_tts_class.return_value.tts_to_file.assert_not_called()


def test_supports_ssml_is_false(mock_tts_class, no_cuda):
    adapter = CoquiTTSAdapter()

    assert adapter.supports_ssml() is False


def test_list_voices_returns_wav_filenames_from_voices_dir(mock_tts_class, no_cuda, tmp_path):
    (tmp_path / "narrator.wav").write_bytes(b"")
    (tmp_path / "second.wav").write_bytes(b"")
    (tmp_path / "notes.txt").write_bytes(b"")

    adapter = CoquiTTSAdapter(voices_dir=str(tmp_path))

    assert sorted(adapter.list_voices()) == ["narrator.wav", "second.wav"]


def test_supports_voice_upload_is_true(mock_tts_class, no_cuda):
    adapter = CoquiTTSAdapter()

    assert adapter.supports_voice_upload() is True


def test_add_voice_writes_file_and_refreshes_list(mock_tts_class, no_cuda, voices_dir):
    adapter = CoquiTTSAdapter(voices_dir=voices_dir)

    adapter.add_voice("second.wav", b"RIFF-fake-wav-bytes")

    assert (Path(voices_dir) / "second.wav").read_bytes() == b"RIFF-fake-wav-bytes"
    assert sorted(adapter.list_voices()) == ["narrator.wav", "second.wav"]


def test_add_voice_rejects_non_wav_filename(mock_tts_class, no_cuda, voices_dir):
    adapter = CoquiTTSAdapter(voices_dir=voices_dir)

    with pytest.raises(ValueError):
        adapter.add_voice("second.mp3", b"not a wav")

    assert not (Path(voices_dir) / "second.mp3").exists()


def test_add_voice_sanitizes_path_traversal_attempt(mock_tts_class, no_cuda, voices_dir):
    adapter = CoquiTTSAdapter(voices_dir=voices_dir)
    escaped_path = Path(voices_dir).parent / "etc" / "passwd.wav"

    adapter.add_voice("../../etc/passwd.wav", b"payload")

    assert (Path(voices_dir) / "passwd.wav").read_bytes() == b"payload"
    assert not escaped_path.exists()


def test_voices_are_fetched_once_at_construction_not_per_call(mock_tts_class, no_cuda, voices_dir):
    """The voice catalog is static for the process's lifetime - caching it in __init__ avoids
    re-listing voices_dir on every synthesize() call in a queue of N tasks."""
    with patch("adapters.driven.tts.coqui_tts_adapter.os.listdir", wraps=os.listdir) as mock_listdir:
        adapter = CoquiTTSAdapter(voices_dir=voices_dir)
        mock_listdir.assert_called_once_with(voices_dir)

        adapter.synthesize(
            content="Hello",
            language="en",
            voice="narrator.wav",
            speed=1.0,
            output_path="out.wav",
        )
        adapter.list_voices()

        mock_listdir.assert_called_once_with(voices_dir)
