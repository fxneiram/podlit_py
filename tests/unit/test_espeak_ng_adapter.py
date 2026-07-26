import subprocess
from unittest.mock import MagicMock, patch

import pytest

from adapters.driven.tts.espeak_ng_adapter import EspeakNGAdapter
from domain.exceptions import TTSEngineUnavailableError, VoiceNotFoundError

VOICES_OUTPUT = (
    "Pty Language       Age/Gender VoiceName          File                 Other Languages\n"
    " 2  en-us           --/M      English_(America)  gmw/en-US            (en 3)\n"
    " 5  es-419          --/M      Spanish_(Latin_America) roa/es-419       (es-mx 6)\n"
)


@pytest.fixture
def mock_run():
    with patch("adapters.driven.tts.espeak_ng_adapter.subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0)
        yield mock


def _voices_result():
    return MagicMock(stdout=VOICES_OUTPUT, returncode=0)


def test_list_voices_parses_file_column(mock_run):
    """Column 4 (File), not VoiceName - `-v` rejects VoiceName values in practice
    (confirmed against the real binary: "Error: The specified espeak-ng voice does not
    exist"), and Language (column 1) isn't guaranteed unique per voice."""
    mock_run.return_value = _voices_result()
    adapter = EspeakNGAdapter()

    assert adapter.list_voices() == ["gmw/en-US", "roa/es-419"]
    mock_run.assert_called_once_with(["espeak-ng", "--voices"], check=True, capture_output=True, text=True)


def test_voices_are_fetched_once_at_construction_not_per_call(mock_run):
    """The voice catalog is static for the process's lifetime - caching it in __init__ avoids
    re-spawning `espeak-ng --voices` on every synthesize() call in a queue of N tasks."""
    mock_run.side_effect = [_voices_result(), MagicMock(returncode=0)]
    adapter = EspeakNGAdapter()

    adapter.synthesize(content="Hello", language="en", voice="gmw/en-US", speed=1.0, output_path="out.wav")
    adapter.list_voices()

    # Only 2 calls total: the --voices fetch in __init__ and the one synthesis call - not a
    # second --voices spawn for validation inside synthesize(), nor a third from list_voices().
    assert mock_run.call_count == 2


def test_synthesize_sends_plain_text_command(mock_run):
    mock_run.side_effect = [_voices_result(), MagicMock(returncode=0)]
    adapter = EspeakNGAdapter()

    adapter.synthesize(
        content="Hello world",
        language="en",
        voice="gmw/en-US",
        speed=1.0,
        output_path="out.wav",
    )

    command = mock_run.call_args_list[1].args[0]
    assert command == ["espeak-ng", "-v", "gmw/en-US", "-s", "175", "-w", "out.wav", "--", "Hello world"]


def test_synthesize_uses_dashdash_so_content_starting_with_dash_is_not_a_flag(mock_run):
    """Confirmed live: without "--", espeak-ng treats a leading "-" in content as an option
    and exits with "invalid option" instead of writing any file."""
    mock_run.side_effect = [_voices_result(), MagicMock(returncode=0)]
    adapter = EspeakNGAdapter()

    adapter.synthesize(
        content="-this looks like a flag",
        language="en",
        voice="gmw/en-US",
        speed=1.0,
        output_path="out.wav",
    )

    command = mock_run.call_args_list[1].args[0]
    assert command[-2:] == ["--", "-this looks like a flag"]


def test_synthesize_converts_speed_to_words_per_minute(mock_run):
    mock_run.side_effect = [_voices_result(), MagicMock(returncode=0)]
    adapter = EspeakNGAdapter()

    adapter.synthesize(
        content="Hello world",
        language="en",
        voice="gmw/en-US",
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
        voice="gmw/en-US",
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
        voice="gmw/en-US",
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
            voice="gmw/en-US",
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
            voice="gmw/en-US",
            speed=1.0,
            output_path="out.wav",
        )


def test_construction_raises_engine_unavailable_when_binary_missing(mock_run):
    """Fetching the voice catalog now happens eagerly at construction, so a missing binary
    fails fast here rather than lazily on the first list_voices()/synthesize() call."""
    mock_run.side_effect = FileNotFoundError("espeak-ng not found")

    with pytest.raises(TTSEngineUnavailableError):
        EspeakNGAdapter()


def test_supports_ssml_is_true(mock_run):
    mock_run.return_value = _voices_result()
    adapter = EspeakNGAdapter()

    assert adapter.supports_ssml() is True
