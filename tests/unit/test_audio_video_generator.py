from unittest.mock import MagicMock, patch

import pytest

from application.ports.tts_port import TextToSpeechPort
from audio_video_generator import AudioVideoGenerator


class FakeTTSAdapter(TextToSpeechPort):
    def __init__(self):
        self.synthesize_calls = []

    def synthesize(self, content, language, voice, speed, output_path, is_ssml=False):
        self.synthesize_calls.append(
            {
                "content": content,
                "language": language,
                "voice": voice,
                "speed": speed,
                "output_path": output_path,
                "is_ssml": is_ssml,
            }
        )

    def list_voices(self):
        return ["narrator.wav", "second.wav"]

    def supports_ssml(self):
        return False


@pytest.fixture
def mocked_media_managers():
    with (
        patch("audio_video_generator.AudioManager") as audio_manager_cls,
        patch("audio_video_generator.VideoManager") as video_manager_cls,
        patch("audio_video_generator.FileManager") as file_manager_cls,
    ):
        file_manager = MagicMock()
        file_manager.generate_random_path.return_value = "task123"
        file_manager.get_final_file_names.return_value = ("output/final.wav", "output/final.mp4")
        file_manager_cls.return_value = file_manager

        yield {
            "audio_manager": audio_manager_cls.return_value,
            "video_manager": video_manager_cls.return_value,
            "file_manager": file_manager,
        }


def test_load_voices_delegates_to_tts_engine(mocked_media_managers):
    generator = AudioVideoGenerator(tts_engine=FakeTTSAdapter())

    voices = generator.load_voices()

    assert voices == ["narrator.wav", "second.wav"]
    assert generator.available_voices == ["narrator.wav", "second.wav"]


def test_change_voice_sets_selected_voice_without_prefixing(mocked_media_managers):
    generator = AudioVideoGenerator(tts_engine=FakeTTSAdapter())

    generator.change_voice("narrator.wav")

    assert generator.selected_voice == "narrator.wav"


@pytest.mark.parametrize(
    "requested_speed,expected",
    [(0.05, 0.1), (1.0, 1.0), (5.0, 3.0)],
)
def test_set_speech_speed_clamps_to_valid_range(mocked_media_managers, requested_speed, expected):
    generator = AudioVideoGenerator(tts_engine=FakeTTSAdapter())

    generator.set_speech_speed(requested_speed)

    assert generator.speech_speed == expected


def test_generate_files_calls_synthesize_once_per_row(mocked_media_managers):
    tts_engine = FakeTTSAdapter()
    generator = AudioVideoGenerator(tts_engine=tts_engine, selected_voice="narrator.wav", speech_speed=1.2)
    text_to_speak = {
        1: {"text": "Hello world.", "language": "en"},
        2: {"text": "Hola mundo.", "language": "es"},
    }

    generator.generate_files(text_to_speak, progress_callback=MagicMock())

    assert len(tts_engine.synthesize_calls) == 2
    assert tts_engine.synthesize_calls[0]["content"] == "Hello world"
    assert tts_engine.synthesize_calls[0]["language"] == "en"
    assert tts_engine.synthesize_calls[0]["voice"] == "narrator.wav"
    assert tts_engine.synthesize_calls[0]["speed"] == 1.2
    assert tts_engine.synthesize_calls[0]["is_ssml"] is False
    assert tts_engine.synthesize_calls[1]["content"] == "Hola mundo"
    assert tts_engine.synthesize_calls[1]["language"] == "es"
