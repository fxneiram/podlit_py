import subprocess

from application.ports.tts_port import TextToSpeechPort
from domain.exceptions import TTSEngineUnavailableError, VoiceNotFoundError

DEFAULT_WORDS_PER_MINUTE = 175
ESPEAK_NG_BINARY = "espeak-ng"


class EspeakNGAdapter(TextToSpeechPort):
    """Shells out to the espeak-ng CLI binary - no server/Docker needed.

    Confirmed by live testing: real Spanish voices (multiple regional variants) and real SSML
    (<speak>, <emphasis>, <break>, <prosody>) both work out of the box, unlike MaryTTSAdapter.
    `language` is accepted (required by the port) but unused - eSpeak-NG's own voice identifiers
    already encode language, so `voice` alone determines it.
    """

    def __init__(self, binary: str = ESPEAK_NG_BINARY):
        self.binary = binary

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
            raise VoiceNotFoundError(f"Voice {voice!r} not found in espeak-ng's voice list")

        words_per_minute = round(DEFAULT_WORDS_PER_MINUTE * speed)
        command = [self.binary, "-v", voice, "-s", str(words_per_minute), "-w", output_path]
        if is_ssml:
            command.append("-m")
        command.append(content)

        try:
            subprocess.run(command, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as error:
            raise TTSEngineUnavailableError(f"espeak-ng failed to synthesize: {error}") from error

    def list_voices(self) -> list[str]:
        try:
            result = subprocess.run([self.binary, "--voices"], check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as error:
            raise TTSEngineUnavailableError(f"espeak-ng --voices failed: {error}") from error

        # Column 4 (File, e.g. "gmw/en-US") is what -v actually accepts - confirmed live.
        # Column 3 (VoiceName, e.g. "English_(America)") looks like an identifier but -v
        # rejects it ("Error: The specified espeak-ng voice does not exist"); column 1
        # (Language, e.g. "en-us") is accepted too but isn't guaranteed unique per voice.
        lines = result.stdout.strip().splitlines()[1:]  # skip the header row
        return [line.split()[4] for line in lines if line.strip()]

    def supports_ssml(self) -> bool:
        return True
