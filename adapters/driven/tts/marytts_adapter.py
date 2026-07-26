import urllib.error
from urllib.parse import urlencode
from urllib.request import urlopen

from application.ports.tts_port import TextToSpeechPort
from domain.exceptions import TTSEngineUnavailableError, VoiceNotFoundError

DEFAULT_BASE_URL = "http://localhost:59125"


class MaryTTSAdapter(TextToSpeechPort):
    """Talks to a local MaryTTS HTTP server. Unlike Coqui, MaryTTS has real SSML support.

    Plain-text speed adjustment is implemented by wrapping the content in a minimal MaryXML
    <prosody rate="..."> envelope, since MaryTTS has no separate numeric speed parameter.
    Caller-supplied SSML (is_ssml=True) is sent verbatim - speed is ignored in that case, since
    rewriting arbitrary SSML to inject a rate risks corrupting it.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url

    def synthesize(
        self,
        content: str,
        language: str,
        voice: str,
        speed: float,
        output_path: str,
        is_ssml: bool = False,
    ) -> None:
        if voice not in self.list_voices():
            raise VoiceNotFoundError(f"Voice {voice!r} not found on MaryTTS server at {self.base_url!r}")

        if is_ssml:
            input_type = "SSML"
            input_text = content
        elif speed != 1.0:
            input_type = "SSML"
            input_text = self._wrap_with_prosody(content, language, speed)
        else:
            input_type = "TEXT"
            input_text = content

        params = {
            "INPUT_TEXT": input_text,
            "INPUT_TYPE": input_type,
            "OUTPUT_TYPE": "AUDIO",
            "AUDIO": "WAVE_FILE",
            "LOCALE": language,
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
        try:
            with urlopen(f"{self.base_url}/voices") as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as error:
            raise TTSEngineUnavailableError(f"MaryTTS server at {self.base_url!r} unreachable: {error}") from error

        return [line.split()[0] for line in body.strip().splitlines() if line.strip()]

    def supports_ssml(self) -> bool:
        return True

    @staticmethod
    def _wrap_with_prosody(content: str, language: str, speed: float) -> str:
        rate_percent = round((speed - 1.0) * 100)
        sign = "+" if rate_percent >= 0 else ""
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<maryxml version="0.5" xml:lang="{language}">'
            f'<prosody rate="{sign}{rate_percent}%">{content}</prosody>'
            "</maryxml>"
        )
