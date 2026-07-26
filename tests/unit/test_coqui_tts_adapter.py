from unittest.mock import MagicMock, patch

import pytest

from adapters.driven.tts.coqui_tts_adapter import CoquiTTSAdapter
from domain.exceptions import SSMLNotSupportedError


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


def test_synthesize_resolves_voice_to_sample_voices_path(mock_tts_class, no_cuda):
    adapter = CoquiTTSAdapter()

    adapter.synthesize(
        content="Hello world",
        language="en",
        voice="narrator.wav",
        speed=1.2,
        output_path="out.wav",
    )

    mock_tts_class.return_value.tts_to_file.assert_called_once_with(
        text="Hello world",
        speaker_wav="sample_voices/narrator.wav",
        language="en",
        file_path="out.wav",
        speed=1.2,
    )


def test_synthesize_raises_when_ssml_requested(mock_tts_class, no_cuda):
    adapter = CoquiTTSAdapter()

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


def test_supports_ssml_is_false(mock_tts_class, no_cuda):
    adapter = CoquiTTSAdapter()

    assert adapter.supports_ssml() is False


def test_list_voices_returns_wav_filenames_from_voices_dir(mock_tts_class, no_cuda, tmp_path):
    (tmp_path / "narrator.wav").write_bytes(b"")
    (tmp_path / "second.wav").write_bytes(b"")
    (tmp_path / "notes.txt").write_bytes(b"")

    adapter = CoquiTTSAdapter(voices_dir=str(tmp_path))

    assert sorted(adapter.list_voices()) == ["narrator.wav", "second.wav"]
