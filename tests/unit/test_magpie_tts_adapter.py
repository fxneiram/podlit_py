"""nemo_toolkit is a ~2.2GB, unstable (@main-branch-only) dependency deliberately not added
to this project's Makefile/CI (see specs/magpie-tts-adapter.md). These tests stub the entire
`nemo` package tree via sys.modules so the real (huge, unstable) package is never required to
run the test suite. MagpieTTSAdapter defers its `nemo` import to __init__, so importing the
adapter module itself (top of this file, like every other adapter test) doesn't need the stub -
only instantiating it does, which each test does inside the `stubbed_nemo` fixture's context.
"""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from adapters.driven.tts.magpie_tts_adapter import MagpieTTSAdapter
from domain.exceptions import SSMLNotSupportedError, VoiceNotFoundError


class FakeMagpieTTSModel:
    num_baked_speakers = 5

    def __init__(self):
        self.do_tts_calls = []
        self.do_tts_return = (MagicMock(), MagicMock())

    @classmethod
    def from_pretrained(cls, model_name, map_location=None):
        return cls()

    def cpu(self):
        return self

    def eval(self):
        return self

    def do_tts(self, transcript, language="en", speaker_index=None):
        self.do_tts_calls.append({"transcript": transcript, "language": language, "speaker_index": speaker_index})
        return self.do_tts_return


@pytest.fixture
def stubbed_nemo():
    fake_module = types.ModuleType("nemo.collections.tts.models")
    fake_module.MagpieTTSModel = FakeMagpieTTSModel
    with patch.dict(
        sys.modules,
        {
            "nemo": types.ModuleType("nemo"),
            "nemo.collections": types.ModuleType("nemo.collections"),
            "nemo.collections.tts": types.ModuleType("nemo.collections.tts"),
            "nemo.collections.tts.models": fake_module,
        },
    ):
        yield fake_module


@pytest.fixture
def mock_torchaudio_save():
    with patch("adapters.driven.tts.magpie_tts_adapter.torchaudio.save") as mock_save:
        yield mock_save


def test_list_voices_derived_from_num_baked_speakers(stubbed_nemo, mock_torchaudio_save):
    adapter = MagpieTTSAdapter()

    assert adapter.list_voices() == ["speaker_0", "speaker_1", "speaker_2", "speaker_3", "speaker_4"]


def test_synthesize_maps_voice_to_speaker_index(stubbed_nemo, mock_torchaudio_save):
    adapter = MagpieTTSAdapter()

    adapter.synthesize(
        content="Hello world",
        language="en",
        voice="speaker_2",
        speed=1.0,
        output_path="out.wav",
    )

    call = adapter.model.do_tts_calls[0]
    assert call["transcript"] == "Hello world"
    assert call["language"] == "en"
    assert call["speaker_index"] == 2


def test_synthesize_accepts_speed_without_effect(stubbed_nemo, mock_torchaudio_save):
    """speed is required by the port but has no effect - MagpieTTS has no speed control."""
    adapter = MagpieTTSAdapter()

    adapter.synthesize(
        content="Hello world",
        language="en",
        voice="speaker_0",
        speed=2.5,
        output_path="out.wav",
    )

    assert len(adapter.model.do_tts_calls) == 1


def test_synthesize_raises_when_ssml_requested(stubbed_nemo, mock_torchaudio_save):
    adapter = MagpieTTSAdapter()

    with pytest.raises(SSMLNotSupportedError):
        adapter.synthesize(
            content="<speak>Hello</speak>",
            language="en",
            voice="speaker_0",
            speed=1.0,
            output_path="out.wav",
            is_ssml=True,
        )

    assert adapter.model.do_tts_calls == []


def test_synthesize_raises_voice_not_found(stubbed_nemo, mock_torchaudio_save):
    adapter = MagpieTTSAdapter()

    with pytest.raises(VoiceNotFoundError):
        adapter.synthesize(
            content="Hello",
            language="en",
            voice="speaker_99",
            speed=1.0,
            output_path="out.wav",
        )


def test_supports_ssml_is_false(stubbed_nemo, mock_torchaudio_save):
    adapter = MagpieTTSAdapter()

    assert adapter.supports_ssml() is False
