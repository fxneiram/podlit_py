import urllib.error
from urllib.parse import urlencode
from urllib.request import urlopen

from application.ports.tts_port import TextToSpeechPort
from domain.exceptions import (
    LanguageNotSupportedError,
    SSMLNotSupportedError,
    TTSEngineUnavailableError,
    VoiceNotFoundError,
    VoiceUploadNotSupportedError,
)

DEFAULT_BASE_URL = "http://localhost:59125"

# Verified live against synesthesiam/marytts:5.2's /locales endpoint - English is the only
# language in this voice set with more than one country variant (en_US/en_GB), so it needs an
# explicit locale; the rest use their bare language code as MaryTTS's own locale identifier.
# There is no Spanish entry: MaryTTS has never shipped an official Spanish voice (a "Jorge"
# attempt was abandoned, unreleased) - confirmed by live testing, not just documentation.
_LANGUAGE_TO_LOCALE = {
    "en": "en_US",
    "de": "de",
    "fr": "fr",
    "it": "it",
    "sv": "sv",
    "ru": "ru",
    "tr": "tr",
}


class MaryTTSAdapter(TextToSpeechPort):
    """Talks to a local MaryTTS HTTP server.

    Known limitations confirmed by live testing against synesthesiam/marytts:5.2 (the only
    published tag for this image, last updated 2020) - not just secondary-source docs:
    - No Spanish voice/locale exists for MaryTTS at all (see _LANGUAGE_TO_LOCALE above).
    - Genuine externally-supplied SSML (INPUT_TYPE=SSML with a <speak> root) throws a
      server-side DOMException on this image - a known, longstanding MaryTTS bug in its
      SSML-to-MaryXML pipeline, not a bug in this adapter's request shape. `supports_ssml()`
      reports False: only this adapter's own RAWMARYXML speed-wrapping path works, and that's
      an internal implementation detail, not "accepts SSML input from the caller" - is_ssml=True
      always raises SSMLNotSupportedError.

    Plain-text speed adjustment is implemented by wrapping the content in a minimal MaryXML
    <prosody rate="..."> envelope sent as RAWMARYXML (not SSML - MaryTTS's SSML parser expects
    genuine SSML, not pre-built MaryXML, and mixing the two throws the same DOMException above).

    The voice catalog is fetched once at construction and cached - it's static for the life of
    a MaryTTS server process, so there's no need to re-fetch it on every synthesize() call.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url
        self._voices = self._fetch_voices()

    def synthesize(
        self,
        content: str,
        language: str,
        voice: str,
        speed: float,
        output_path: str,
        is_ssml: bool = False,
    ) -> None:
        if is_ssml:
            raise SSMLNotSupportedError(
                "MaryTTSAdapter does not support caller-supplied SSML "
                "(genuine SSML input is broken on synesthesiam/marytts:5.2)"
            )

        if voice not in self._voices:
            raise VoiceNotFoundError(f"Voice {voice!r} not found on MaryTTS server at {self.base_url!r}")

        locale = _LANGUAGE_TO_LOCALE.get(language)
        if locale is None:
            raise LanguageNotSupportedError(f"MaryTTS has no locale mapping for language {language!r}")

        if speed != 1.0:
            input_type = "RAWMARYXML"
            input_text = self._wrap_with_prosody(content, locale, speed)
        else:
            input_type = "TEXT"
            input_text = content

        params = {
            "INPUT_TEXT": input_text,
            "INPUT_TYPE": input_type,
            "OUTPUT_TYPE": "AUDIO",
            "AUDIO": "WAVE_FILE",
            "LOCALE": locale,
            "VOICE": voice,
        }

        try:
            with urlopen(f"{self.base_url}/process?{urlencode(params)}") as response:
                audio_bytes = response.read()
        except urllib.error.URLError as error:
            raise TTSEngineUnavailableError(f"MaryTTS server at {self.base_url!r} unreachable: {error}") from error

        with open(output_path, "wb") as output_file:
            output_file.write(audio_bytes)

    def list_voices(self) -> list[str]:
        return self._voices

    def supports_ssml(self) -> bool:
        return False

    def supports_voice_upload(self) -> bool:
        return False

    def add_voice(self, filename: str, content: bytes) -> None:
        raise VoiceUploadNotSupportedError("MaryTTSAdapter uses server-side installed voices, no sample upload")

    def _fetch_voices(self) -> list[str]:
        try:
            with urlopen(f"{self.base_url}/voices") as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as error:
            raise TTSEngineUnavailableError(f"MaryTTS server at {self.base_url!r} unreachable: {error}") from error

        return [line.split()[0] for line in body.strip().splitlines() if line.strip()]

    @staticmethod
    def _wrap_with_prosody(content: str, locale: str, speed: float) -> str:
        rate_percent = round((speed - 1.0) * 100)
        sign = "+" if rate_percent >= 0 else ""
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<maryxml version="0.5" xml:lang="{locale}">'
            f'<prosody rate="{sign}{rate_percent}%">{content}</prosody>'
            "</maryxml>"
        )
