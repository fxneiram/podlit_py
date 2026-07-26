from abc import ABC, abstractmethod


class TextToSpeechPort(ABC):
    """Contract any TTS engine adapter must implement.

    `voice` and `speed` are passed per call rather than kept as adapter state, so the port
    stays a pure capability contract and is trivial to fake in tests.
    """

    @abstractmethod
    def synthesize(
        self,
        content: str,
        language: str,
        voice: str,
        speed: float,
        output_path: str,
        is_ssml: bool = False,
    ) -> None:
        """Write synthesized audio for `content` to `output_path`.

        Raises:
            SSMLNotSupportedError: if `is_ssml` is True and `supports_ssml()` is False.
            VoiceNotFoundError: if `voice` isn't one of `list_voices()`.
        """

    @abstractmethod
    def list_voices(self) -> list[str]:
        """Return the identifiers of voices this engine can use."""

    @abstractmethod
    def supports_ssml(self) -> bool:
        """Whether this engine can accept `is_ssml=True` input."""
