from typing import Protocol

from application.ports.tts_port import TextToSpeechPort
from domain.exceptions import VoiceNotFoundError


class VoiceSettingsManager(Protocol):
    """Structural contract for the collaborator whose voice/speed settings this use case
    manages - matches AudioVideoGenerator's public shape without requiring inheritance from it,
    so tests can supply a lightweight fake."""

    def load_voices(self) -> list[str]: ...

    def change_voice(self, voice: str) -> None: ...

    def set_speech_speed(self, speed: float) -> None: ...


class ManageVoicesUseCase:
    """Exposes voice listing/upload/selection and speech-speed control - what
    AudioVideoGenerator.load_voices/change_voice/set_speech_speed already do, plus uploading a
    new voice sample (a capability the Tkinter UI never had)."""

    def __init__(self, tts_engine: TextToSpeechPort, media_generator: VoiceSettingsManager):
        self._tts_engine = tts_engine
        self._media_generator = media_generator

    def list_voices(self) -> list[str]:
        return self._media_generator.load_voices()

    def upload_voice(self, filename: str, content: bytes) -> None:
        self._tts_engine.add_voice(filename, content)
        self._media_generator.load_voices()

    def select_voice(self, voice: str) -> None:
        if voice not in self._media_generator.load_voices():
            raise VoiceNotFoundError(f"Voice {voice!r} not found")
        self._media_generator.change_voice(voice)

    def set_speed(self, speed: float) -> None:
        self._media_generator.set_speech_speed(speed)
