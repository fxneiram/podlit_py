import wave
from unittest.mock import MagicMock, patch

from adapters.driven.tts.espeak_ng_adapter import EspeakNGAdapter
from audio_video_generator import AudioVideoGenerator


def test_audio_video_generator_drives_the_real_espeak_ng_adapter(tmp_path):
    """Unlike the Coqui/MaryTTS wiring tests, nothing here is stubbed except the unrelated
    audio/video managers - espeak-ng is a fast, lightweight, already-installed local binary
    with no server or heavy model to mock, so this exercises the real subprocess call and
    produces a real, valid WAV file.
    """
    with (
        patch("audio_video_generator.AudioManager"),
        patch("audio_video_generator.VideoManager"),
        patch("audio_video_generator.FileManager") as mock_file_manager_cls,
        patch("audio_video_generator.cfg.TEMP_DIR", str(tmp_path)),
    ):
        mock_file_manager = MagicMock()
        mock_file_manager.generate_random_path.return_value = "task123"
        mock_file_manager.get_final_file_names.return_value = (
            str(tmp_path / "final.wav"),
            str(tmp_path / "final.mp4"),
        )
        mock_file_manager_cls.return_value = mock_file_manager

        tts_engine = EspeakNGAdapter()
        available_voice = tts_engine.list_voices()[0]
        generator = AudioVideoGenerator(tts_engine=tts_engine, selected_voice=available_voice, speech_speed=1.0)
        text_to_speak = {1: {"text": "Hello world.", "language": "en"}}

        generator.generate_files(text_to_speak, progress_callback=MagicMock())

        generated_audio_path = tmp_path / "task123_tmp_0_a.wav"
        assert generated_audio_path.exists()
        with wave.open(str(generated_audio_path), "rb") as wav_file:
            assert wav_file.getnframes() > 0
