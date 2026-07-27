import pytest

from application.use_cases.manage_voices_use_case import ManageVoicesUseCase
from domain.exceptions import VoiceNotFoundError, VoiceUploadNotSupportedError


class FakeTTSEngine:
    def __init__(self, voices=None, upload_supported=True):
        self._voices = voices or ["narrator.wav"]
        self._upload_supported = upload_supported
        self.add_voice_calls = []

    def list_voices(self):
        return self._voices

    def supports_voice_upload(self):
        return self._upload_supported

    def add_voice(self, filename, content):
        if not self._upload_supported:
            raise VoiceUploadNotSupportedError("upload not supported")
        self.add_voice_calls.append((filename, content))
        self._voices.append(filename)


class FakeMediaGenerator:
    def __init__(self, tts_engine):
        self._tts_engine = tts_engine
        self.selected_voice = None
        self.speech_speed = 1.0

    def load_voices(self):
        return self._tts_engine.list_voices()

    def change_voice(self, voice):
        self.selected_voice = voice

    def set_speech_speed(self, speed):
        self.speech_speed = max(0.1, min(3.0, speed))


@pytest.fixture
def tts_engine():
    return FakeTTSEngine()


@pytest.fixture
def media_generator(tts_engine):
    return FakeMediaGenerator(tts_engine)


@pytest.fixture
def use_case(tts_engine, media_generator):
    return ManageVoicesUseCase(tts_engine=tts_engine, media_generator=media_generator)


def test_list_voices_returns_the_current_catalog(use_case):
    assert use_case.list_voices() == ["narrator.wav"]


def test_upload_voice_delegates_to_the_engine_and_refreshes_the_list(use_case, tts_engine):
    use_case.upload_voice("second.wav", b"content")

    assert tts_engine.add_voice_calls == [("second.wav", b"content")]
    assert use_case.list_voices() == ["narrator.wav", "second.wav"]


def test_upload_voice_raises_when_engine_does_not_support_it(tts_engine, media_generator):
    tts_engine = FakeTTSEngine(upload_supported=False)
    use_case = ManageVoicesUseCase(tts_engine=tts_engine, media_generator=FakeMediaGenerator(tts_engine))

    with pytest.raises(VoiceUploadNotSupportedError):
        use_case.upload_voice("second.wav", b"content")


def test_select_voice_changes_the_active_voice(use_case, media_generator):
    use_case.select_voice("narrator.wav")

    assert media_generator.selected_voice == "narrator.wav"


def test_select_voice_raises_when_voice_not_in_catalog(use_case):
    with pytest.raises(VoiceNotFoundError):
        use_case.select_voice("missing.wav")


def test_set_speed_updates_the_media_generator(use_case, media_generator):
    use_case.set_speed(1.5)

    assert media_generator.speech_speed == 1.5


def test_set_speed_relies_on_media_generator_clamping(use_case, media_generator):
    """set_speech_speed already clamps to [0.1, 3.0] - the use case doesn't duplicate that
    validation, it just forwards the value."""
    use_case.set_speed(10.0)

    assert media_generator.speech_speed == 3.0
