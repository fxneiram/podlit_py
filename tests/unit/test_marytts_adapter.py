import urllib.error
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from adapters.driven.tts.marytts_adapter import MaryTTSAdapter
from domain.exceptions import LanguageNotSupportedError, TTSEngineUnavailableError, VoiceNotFoundError

VOICES_RESPONSE = b"alice-hsmm en_US female\nbits3-hsmm en_US male\n"


def _mock_response(body: bytes):
    response = MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


@pytest.fixture
def mock_urlopen():
    with patch("adapters.driven.tts.marytts_adapter.urlopen") as mock:
        yield mock


def _query_params(url: str) -> dict:
    return {key: values[0] for key, values in parse_qs(urlparse(url).query).items()}


def test_list_voices_parses_names_from_response(mock_urlopen):
    mock_urlopen.return_value = _mock_response(VOICES_RESPONSE)
    adapter = MaryTTSAdapter()

    assert adapter.list_voices() == ["alice-hsmm", "bits3-hsmm"]
    mock_urlopen.assert_called_once_with("http://localhost:59125/voices")


def test_synthesize_sends_plain_text_when_speed_is_default(mock_urlopen, tmp_path):
    mock_urlopen.side_effect = [_mock_response(VOICES_RESPONSE), _mock_response(b"WAV-BYTES")]
    output_path = tmp_path / "out.wav"
    adapter = MaryTTSAdapter()

    adapter.synthesize(
        content="Hello world",
        language="en",
        voice="alice-hsmm",
        speed=1.0,
        output_path=str(output_path),
    )

    process_url = mock_urlopen.call_args_list[1].args[0]
    params = _query_params(process_url)
    assert params["INPUT_TYPE"] == "TEXT"
    assert params["INPUT_TEXT"] == "Hello world"
    assert params["LOCALE"] == "en_US"
    assert params["VOICE"] == "alice-hsmm"
    assert params["OUTPUT_TYPE"] == "AUDIO"
    assert params["AUDIO"] == "WAVE_FILE"
    assert output_path.read_bytes() == b"WAV-BYTES"


def test_synthesize_wraps_rawmaryxml_prosody_when_speed_adjusted(mock_urlopen, tmp_path):
    """RAWMARYXML, not SSML: MaryTTS's SSML parser expects genuine SSML and throws a
    server-side DOMException on a pre-built MaryXML document tagged as SSML (confirmed by
    live testing against synesthesiam/marytts:5.2)."""
    mock_urlopen.side_effect = [_mock_response(VOICES_RESPONSE), _mock_response(b"WAV-BYTES")]
    output_path = tmp_path / "out.wav"
    adapter = MaryTTSAdapter()

    adapter.synthesize(
        content="Hello world",
        language="en",
        voice="alice-hsmm",
        speed=1.2,
        output_path=str(output_path),
    )

    params = _query_params(mock_urlopen.call_args_list[1].args[0])
    assert params["INPUT_TYPE"] == "RAWMARYXML"
    assert "Hello world" in params["INPUT_TEXT"]
    assert 'rate="+20%"' in params["INPUT_TEXT"]


def test_synthesize_passes_through_caller_ssml_verbatim(mock_urlopen, tmp_path):
    mock_urlopen.side_effect = [_mock_response(VOICES_RESPONSE), _mock_response(b"WAV-BYTES")]
    output_path = tmp_path / "out.wav"
    adapter = MaryTTSAdapter()
    caller_ssml = "<speak>Hello <emphasis>world</emphasis></speak>"

    adapter.synthesize(
        content=caller_ssml,
        language="en",
        voice="alice-hsmm",
        speed=1.0,
        output_path=str(output_path),
        is_ssml=True,
    )

    params = _query_params(mock_urlopen.call_args_list[1].args[0])
    assert params["INPUT_TYPE"] == "SSML"
    assert params["INPUT_TEXT"] == caller_ssml


def test_synthesize_ignores_speed_when_caller_provides_ssml(mock_urlopen, tmp_path):
    mock_urlopen.side_effect = [_mock_response(VOICES_RESPONSE), _mock_response(b"WAV-BYTES")]
    output_path = tmp_path / "out.wav"
    adapter = MaryTTSAdapter()
    caller_ssml = "<speak>Hello</speak>"

    adapter.synthesize(
        content=caller_ssml,
        language="en",
        voice="alice-hsmm",
        speed=1.5,
        output_path=str(output_path),
        is_ssml=True,
    )

    params = _query_params(mock_urlopen.call_args_list[1].args[0])
    assert params["INPUT_TEXT"] == caller_ssml


def test_synthesize_raises_voice_not_found(mock_urlopen, tmp_path):
    mock_urlopen.return_value = _mock_response(VOICES_RESPONSE)
    adapter = MaryTTSAdapter()

    with pytest.raises(VoiceNotFoundError):
        adapter.synthesize(
            content="Hello",
            language="en",
            voice="missing-voice",
            speed=1.0,
            output_path=str(tmp_path / "out.wav"),
        )


def test_synthesize_raises_engine_unavailable_on_connection_error(mock_urlopen, tmp_path):
    mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
    adapter = MaryTTSAdapter()

    with pytest.raises(TTSEngineUnavailableError):
        adapter.synthesize(
            content="Hello",
            language="en",
            voice="alice-hsmm",
            speed=1.0,
            output_path=str(tmp_path / "out.wav"),
        )


def test_list_voices_raises_engine_unavailable_on_connection_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
    adapter = MaryTTSAdapter()

    with pytest.raises(TTSEngineUnavailableError):
        adapter.list_voices()


def test_supports_ssml_is_true(mock_urlopen):
    adapter = MaryTTSAdapter()

    assert adapter.supports_ssml() is True


def test_synthesize_raises_language_not_supported_for_spanish(mock_urlopen, tmp_path):
    """MaryTTS has never shipped an official Spanish voice - confirmed by live testing
    against synesthesiam/marytts:5.2's /locales endpoint, not just secondary documentation.
    This is a real, permanent limitation for this project's bilingual EN/ES use case."""
    mock_urlopen.return_value = _mock_response(VOICES_RESPONSE)
    adapter = MaryTTSAdapter()

    with pytest.raises(LanguageNotSupportedError):
        adapter.synthesize(
            content="Hola mundo",
            language="es",
            voice="alice-hsmm",
            speed=1.0,
            output_path=str(tmp_path / "out.wav"),
        )
