import urllib.error
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from adapters.driven.tts.marytts_adapter import MaryTTSAdapter
from domain.exceptions import (
    LanguageNotSupportedError,
    SSMLNotSupportedError,
    TTSEngineUnavailableError,
    VoiceNotFoundError,
    VoiceUploadNotSupportedError,
)

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


def test_voices_are_fetched_once_at_construction_not_per_call(mock_urlopen, tmp_path):
    """The voice catalog is static for the life of a MaryTTS server process - caching it in
    __init__ avoids an HTTP round-trip on every synthesize() call in a queue of N tasks."""
    mock_urlopen.side_effect = [_mock_response(VOICES_RESPONSE), _mock_response(b"WAV-BYTES")]
    adapter = MaryTTSAdapter()

    adapter.synthesize(
        content="Hello",
        language="en",
        voice="alice-hsmm",
        speed=1.0,
        output_path=str(tmp_path / "out.wav"),
    )
    adapter.list_voices()

    # Only 2 calls total: the /voices fetch in __init__ and the one /process call - not a
    # second /voices call for validation inside synthesize(), nor a third from list_voices().
    assert mock_urlopen.call_count == 2


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


def test_synthesize_raises_ssml_not_supported(mock_urlopen, tmp_path):
    """supports_ssml() is False: genuine SSML input is broken on synesthesiam/marytts:5.2
    (confirmed by live testing), so is_ssml=True always raises rather than attempting a
    request that's known to fail server-side."""
    mock_urlopen.return_value = _mock_response(VOICES_RESPONSE)
    adapter = MaryTTSAdapter()

    with pytest.raises(SSMLNotSupportedError):
        adapter.synthesize(
            content="<speak>Hello <emphasis>world</emphasis></speak>",
            language="en",
            voice="alice-hsmm",
            speed=1.0,
            output_path=str(tmp_path / "out.wav"),
            is_ssml=True,
        )

    # Only the /voices fetch from __init__ - no /process call attempted.
    assert mock_urlopen.call_count == 1


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


def test_construction_raises_engine_unavailable_on_connection_error(mock_urlopen):
    """Fetching the voice catalog now happens eagerly at construction, so an unreachable
    server fails fast here rather than lazily on the first synthesize() call."""
    mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

    with pytest.raises(TTSEngineUnavailableError):
        MaryTTSAdapter()


def test_supports_ssml_is_false(mock_urlopen):
    mock_urlopen.return_value = _mock_response(VOICES_RESPONSE)
    adapter = MaryTTSAdapter()

    assert adapter.supports_ssml() is False


def test_supports_voice_upload_is_false(mock_urlopen):
    mock_urlopen.return_value = _mock_response(VOICES_RESPONSE)
    adapter = MaryTTSAdapter()

    assert adapter.supports_voice_upload() is False


def test_add_voice_raises_voice_upload_not_supported(mock_urlopen):
    mock_urlopen.return_value = _mock_response(VOICES_RESPONSE)
    adapter = MaryTTSAdapter()

    with pytest.raises(VoiceUploadNotSupportedError):
        adapter.add_voice("alice-hsmm.wav", b"content")


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
