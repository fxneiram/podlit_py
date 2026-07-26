import os

import torch
from TTS.api import TTS

from application.ports.tts_port import TextToSpeechPort
from domain.exceptions import SSMLNotSupportedError, VoiceNotFoundError

XTTS_V2_MODEL_PATH = "tts_models/multilingual/multi-dataset/xtts_v2"


class CoquiTTSAdapter(TextToSpeechPort):
    """Wraps Coqui XTTS v2. XTTS v2 has no SSML input path at the model level."""

    def __init__(self, voices_dir: str = "sample_voices"):
        self.voices_dir = voices_dir
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = TTS(XTTS_V2_MODEL_PATH, progress_bar=False).to(device)

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
            raise SSMLNotSupportedError("CoquiTTSAdapter (XTTS v2) does not support SSML input")

        if voice not in self.list_voices():
            raise VoiceNotFoundError(f"Voice {voice!r} not found in {self.voices_dir!r}")

        speaker_wav = os.path.join(self.voices_dir, voice)
        self.tts.tts_to_file(
            text=content,
            speaker_wav=speaker_wav,
            language=language,
            file_path=output_path,
            speed=speed,
        )

    def list_voices(self) -> list[str]:
        return [name for name in os.listdir(self.voices_dir) if name.endswith(".wav")]

    def supports_ssml(self) -> bool:
        return False
