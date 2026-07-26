import torch
import torchaudio

from application.ports.tts_port import TextToSpeechPort
from domain.exceptions import SSMLNotSupportedError, VoiceNotFoundError

MAGPIE_MODEL_NAME = "nvidia/magpie_tts_multilingual_357m"
SAMPLE_RATE = 22050


class MagpieTTSAdapter(TextToSpeechPort):
    """Wraps NVIDIA's MagpieTTS (NeMo). Confirmed by live testing: runs on CPU (~4x slower
    than real-time - workable for this project's background queue, not real-time use), with
    genuine neural quality and real Spanish support.

    Requires `nemo_toolkit[tts]` (from its `main` git branch - the stable PyPI release fails to
    load this checkpoint) and `torchcodec` (a fresh, unpinned `torchaudio` needs it for
    `.save()`). This is a large (~2.2GB), unpinned dependency deliberately NOT added to this
    project's Makefile/CI (see specs/magpie-tts-adapter.md) - use `make install-magpie`, ideally
    in a separate conda env/venv from your main `tts` env: nemo_toolkit's own unpinned
    requirements can upgrade the CPU-pinned torch/torchaudio (and possibly numpy==1.26.4) that
    `make install-deps` set up for Coqui/eSpeak-NG.

    Deliberate limitation, confirmed with the user: MagpieTTS's public API has NO prosody
    control whatsoever - no SSML, no style/tone description, not even a numeric speed knob.
    `speed` is accepted (required by the port) but has no effect. `is_ssml=True` raises
    SSMLNotSupportedError.
    """

    def __init__(self, model_name: str = MAGPIE_MODEL_NAME):
        from nemo.collections.tts.models import MagpieTTSModel

        self.model = MagpieTTSModel.from_pretrained(model_name, map_location="cpu")
        self.model = self.model.cpu()
        self.model.eval()

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
            raise SSMLNotSupportedError("MagpieTTSAdapter does not support SSML input")

        if voice not in self.list_voices():
            raise VoiceNotFoundError(f"Voice {voice!r} not found - available: {self.list_voices()}")

        speaker_index = self._voice_to_speaker_index(voice)

        with torch.no_grad():
            audio, audio_len = self.model.do_tts(content, language=language, speaker_index=speaker_index)

        torchaudio.save(output_path, audio[:, : audio_len[0]].cpu(), SAMPLE_RATE)

    def list_voices(self) -> list[str]:
        return [f"speaker_{i}" for i in range(self.model.num_baked_speakers)]

    def supports_ssml(self) -> bool:
        return False

    @staticmethod
    def _voice_to_speaker_index(voice: str) -> int:
        return int(voice.removeprefix("speaker_"))
