from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from adapters.driven.tts.marytts_adapter import MaryTTSAdapter
from audio_video_generator import AudioVideoGenerator

VOICES_RESPONSE = b"alice-hsmm en_US female\n"


def _mock_response(body: bytes):
    response = MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_audio_video_generator_drives_the_real_marytts_adapter(tmp_path):
    """Wires the real MaryTTSAdapter (not a hand-written fake) into AudioVideoGenerator to
    catch drift between what AudioVideoGenerator calls and what the concrete adapter expects.
    Only the HTTP boundary to the MaryTTS server is stubbed - everything else is real.
    """
    with (
        patch("adapters.driven.tts.marytts_adapter.urlopen") as mock_urlopen,
        patch("audio_video_generator.AudioManager"),
        patch("audio_video_generator.VideoManager"),
        patch("audio_video_generator.FileManager") as mock_file_manager_cls,
        patch("audio_video_generator.cfg.TEMP_DIR", str(tmp_path)),
    ):
        # MaryTTSAdapter.__init__ fetches /voices once and caches it; AudioVideoGenerator's
        # own load_voices() and synthesize()'s voice validation both hit that cache, so only
        # one more call (/process) happens after construction.
        mock_urlopen.side_effect = [
            _mock_response(VOICES_RESPONSE),
            _mock_response(b"WAV-BYTES"),
        ]

        mock_file_manager = MagicMock()
        mock_file_manager.generate_random_path.return_value = "task123"
        audio_path = tmp_path / "final.wav"
        mock_file_manager.get_final_file_names.return_value = (str(audio_path), str(tmp_path / "final.mp4"))
        mock_file_manager_cls.return_value = mock_file_manager

        tts_engine = MaryTTSAdapter()
        generator = AudioVideoGenerator(tts_engine=tts_engine, selected_voice="alice-hsmm", speech_speed=1.0)
        text_to_speak = {1: {"text": "Hello world.", "language": "en"}}

        generator.generate_files(text_to_speak, progress_callback=MagicMock())

        process_url = mock_urlopen.call_args_list[1].args[0]
        params = {key: values[0] for key, values in parse_qs(urlparse(process_url).query).items()}
        assert params["INPUT_TEXT"] == "Hello world"
        assert params["INPUT_TYPE"] == "TEXT"
        assert params["LOCALE"] == "en_US"
        assert params["VOICE"] == "alice-hsmm"
