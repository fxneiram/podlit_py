import sys
import types
from unittest.mock import MagicMock, patch

from tests.unit.test_magpie_tts_adapter import FakeMagpieTTSModel


def test_audio_video_generator_drives_the_magpie_adapter(tmp_path):
    """Same reasoning as the MagpieTTSAdapter unit tests: nemo_toolkit is too heavy/unstable
    to install in CI, so the entire `nemo` package is stubbed rather than mocking one real
    call - the same pattern used for the unit tests, applied here to prove the wiring through
    AudioVideoGenerator works too.
    """
    fake_module = types.ModuleType("nemo.collections.tts.models")
    fake_module.MagpieTTSModel = FakeMagpieTTSModel

    with (
        patch.dict(
            sys.modules,
            {
                "nemo": types.ModuleType("nemo"),
                "nemo.collections": types.ModuleType("nemo.collections"),
                "nemo.collections.tts": types.ModuleType("nemo.collections.tts"),
                "nemo.collections.tts.models": fake_module,
            },
        ),
        patch("adapters.driven.tts.magpie_tts_adapter.torchaudio.save") as mock_save,
        patch("audio_video_generator.AudioManager"),
        patch("audio_video_generator.VideoManager"),
        patch("audio_video_generator.FileManager") as mock_file_manager_cls,
        patch("audio_video_generator.cfg.TEMP_DIR", str(tmp_path)),
    ):
        from adapters.driven.tts.magpie_tts_adapter import MagpieTTSAdapter
        from audio_video_generator import AudioVideoGenerator

        mock_file_manager = MagicMock()
        mock_file_manager.generate_random_path.return_value = "task123"
        mock_file_manager.get_final_file_names.return_value = (
            str(tmp_path / "final.wav"),
            str(tmp_path / "final.mp4"),
        )
        mock_file_manager_cls.return_value = mock_file_manager

        tts_engine = MagpieTTSAdapter()
        generator = AudioVideoGenerator(tts_engine=tts_engine, selected_voice="speaker_0", speech_speed=1.0)
        text_to_speak = {1: {"text": "Hello world.", "language": "en"}}

        generator.generate_files(text_to_speak, progress_callback=MagicMock())

        assert tts_engine.model.do_tts_calls[0]["transcript"] == "Hello world"
        assert tts_engine.model.do_tts_calls[0]["speaker_index"] == 0
        mock_save.assert_called_once()
