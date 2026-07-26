import subprocess
from unittest.mock import MagicMock, patch

import pytest

from adapters.driven.tts.espeak_ng_adapter import EspeakNGAdapter
from domain.exceptions import TTSEngineUnavailableError, VoiceNotFoundError

VOICES_OUTPUT = (
    "Pty Language       Age/Gender VoiceName          File                 Other Languages\n"
    " 5  en-us           --/M      English_(America)  en/en-us             \n"
    " 5  es-419          --/M      Spanish_(Latin_America) roa/es-419       \n"
)


@pytest.fixture
def mock_run():
    with patch("adapters.driven.tts.espeak_ng_adapter.subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0)
        yield mock


def _voices_result():
    return MagicMock(stdout=VOICES_OUTPUT, returncode=0)


def test_list_voices_parses_voice_name_column(mock_run):
    mock_run.return_value = _voices_result()
    adapter = EspeakNGAdapter()

    assert adapter.list_voices() == ["English_(America)", "Spanish_(Latin_America)"]
    mock_run.assert_called_once_with(["espeak-ng", "--voices"], check=True, capture_output=True, text=True)


def test_synthesize_sends_plain_text_command(mock_run):
    mock_run.side_effect = [_voices_result(), MagicMock(returncode=0)]
    adapter = EspeakNGAdapter()

    adapter.synthesize(
        content="Hello world",
        language="en",
        voice="English_(America)",
        speed=1.0,
        output_path="out.wav",
    )

    command = mock_run.call_args_list[1].args[0]
    assert command == ["espeak-ng", "-v", "English_(America)", "-s", "175", "-w", "out.wav", "Hello world"]


def test_synthesize_converts_speed_to_words_per_minute(mock_run):
    mock_run.side_effect = [_voices_result(), MagicMock(returncode=0)]
    adapter = EspeakNGAdapter()

    adapter.synthesize(
        content="Hello world",
        language="en",
        voice="English_(America)",
        speed=1.2,
        output_path="out.wav",
    )

    command = mock_run.call_args_list[1].args[0]
    assert "-s" in command
    assert command[command.index("-s") + 1] == "210"


def test_synthesize_adds_markup_flag_for_ssml(mock_run):
    mock_run.side_effect = [_voices_result(), MagicMock(returncode=0)]
    adapter = EspeakNGAdapter()

    adapter.synthesize(
        content="<speak>Hello <emphasis>world</emphasis></speak>",
        language="en",
        voice="English_(America)",
        speed=1.0,
        output_path="out.wav",
        is_ssml=True,
    )

    command = mock_run.call_args_list[1].args[0]
    assert "-m" in command
    assert command[-1] == "<speak>Hello <emphasis>world</emphasis></speak>"


def test_synthesize_combines_speed_and_ssml(mock_run):
    """Unlike MaryTTSAdapter, speed is NOT ignored under is_ssml=True - -s and -m compose
    without conflict (confirmed by live testing against the real espeak-ng binary)."""
    mock_run.side_effect = [_voices_result(), MagicMock(returncode=0)]
    adapter = EspeakNGAdapter()

    adapter.synthesize(
        content="<speak>Hello</speak>",
        language="en",
        voice="English_(America)",
        speed=1.4,
        output_path="out.wav",
        is_ssml=True,
    )

    command = mock_run.call_args_list[1].args[0]
    assert "-m" in command
    assert command[command.index("-s") + 1] == "245"


def test_synthesize_raises_voice_not_found(mock_run):
    mock_run.return_value = _voices_result()
    adapter = EspeakNGAdapter()

    with pytest.raises(VoiceNotFoundError):
        adapter.synthesize(
            content="Hello",
            language="en",
            voice="missing-voice",
            speed=1.0,
            output_path="out.wav",
        )


def test_synthesize_raises_engine_unavailable_on_process_error(mock_run):
    mock_run.side_effect = [_voices_result(), subprocess.CalledProcessError(1, ["espeak-ng"])]
    adapter = EspeakNGAdapter()

    with pytest.raises(TTSEngineUnavailableError):
        adapter.synthesize(
            content="Hello",
            language="en",
            voice="English_(America)",
            speed=1.0,
            output_path="out.wav",
        )


def test_synthesize_raises_engine_unavailable_when_binary_missing(mock_run):
    mock_run.side_effect = [_voices_result(), FileNotFoundError("espeak-ng not found")]
    adapter = EspeakNGAdapter()

    with pytest.raises(TTSEngineUnavailableError):
        adapter.synthesize(
            content="Hello",
            language="en",
            voice="English_(America)",
            speed=1.0,
            output_path="out.wav",
        )


def test_list_voices_raises_engine_unavailable_when_binary_missing(mock_run):
    mock_run.side_effect = FileNotFoundError("espeak-ng not found")
    adapter = EspeakNGAdapter()

    with pytest.raises(TTSEngineUnavailableError):
        adapter.list_voices()


def test_supports_ssml_is_true(mock_run):
    adapter = EspeakNGAdapter()

    assert adapter.supports_ssml() is True
