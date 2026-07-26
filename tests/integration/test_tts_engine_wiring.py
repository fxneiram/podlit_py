from unittest.mock import MagicMock, patch

from adapters.driven.tts.coqui_tts_adapter import CoquiTTSAdapter
from audio_video_generator import AudioVideoGenerator


def test_audio_video_generator_drives_the_real_coqui_adapter():
    """Wires the real CoquiTTSAdapter (not a hand-written fake) into AudioVideoGenerator,
    the way app.py does, to catch any drift between what AudioVideoGenerator calls and what
    the concrete adapter actually expects. Only the expensive model load/inference is stubbed.
    """
    with (
        patch("adapters.driven.tts.coqui_tts_adapter.TTS") as mock_tts_class,
        patch("adapters.driven.tts.coqui_tts_adapter.torch.cuda.is_available", return_value=False),
        patch("audio_video_generator.AudioManager"),
        patch("audio_video_generator.VideoManager"),
        patch("audio_video_generator.FileManager") as mock_file_manager_cls,
    ):
        mock_tts_instance = MagicMock()
        mock_tts_instance.to.return_value = mock_tts_instance
        mock_tts_class.return_value = mock_tts_instance

        mock_file_manager = MagicMock()
        mock_file_manager.generate_random_path.return_value = "task123"
        mock_file_manager.get_final_file_names.return_value = ("output/final.wav", "output/final.mp4")
        mock_file_manager_cls.return_value = mock_file_manager

        tts_engine = CoquiTTSAdapter()
        generator = AudioVideoGenerator(tts_engine=tts_engine, selected_voice="narrator.wav", speech_speed=1.0)
        text_to_speak = {1: {"text": "Hello world.", "language": "en"}}

        generator.generate_files(text_to_speak, progress_callback=MagicMock())

        mock_tts_instance.tts_to_file.assert_called_once()
        call_kwargs = mock_tts_instance.tts_to_file.call_args.kwargs
        assert call_kwargs["text"] == "Hello world"
        assert call_kwargs["language"] == "en"
        assert call_kwargs["speaker_wav"] == "sample_voices/narrator.wav"
        assert call_kwargs["speed"] == 1.0
