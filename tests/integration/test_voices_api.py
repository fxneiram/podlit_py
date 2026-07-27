"""Real FastAPI TestClient (including a real multipart upload) against a fake TTS engine/media
generator - only the actual TTS model and filesystem writes are faked, per this project's "don't
touch real TTS/audio in tests" pattern.
"""

import pytest
from fastapi.testclient import TestClient

from adapters.driven.persistence.json_task_repository import JsonTaskRepository
from adapters.driving.api.app import create_app
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase
from application.use_cases.manage_voices_use_case import ManageVoicesUseCase
from domain.exceptions import VoiceUploadNotSupportedError


class FakeTTSEngine:
    def __init__(self, voices=None, upload_supported=True):
        self._voices = voices or ["narrator.wav"]
        self._upload_supported = upload_supported

    def list_voices(self):
        return self._voices

    def supports_voice_upload(self):
        return self._upload_supported

    def add_voice(self, filename, content):
        if not self._upload_supported:
            raise VoiceUploadNotSupportedError("upload not supported")
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
def wiring(tmp_path):
    repository = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))
    use_case = ManageTaskQueueUseCase(repository=repository)
    tts_engine = FakeTTSEngine()
    media_generator = FakeMediaGenerator(tts_engine)
    manage_voices_use_case = ManageVoicesUseCase(tts_engine=tts_engine, media_generator=media_generator)
    app = create_app(use_case, manage_voices_use_case=manage_voices_use_case)
    return TestClient(app), tts_engine, media_generator


def test_get_voices_returns_the_current_catalog(wiring):
    client, _tts_engine, _media_generator = wiring

    response = client.get("/voices")

    assert response.status_code == 200
    assert response.json() == {"voices": ["narrator.wav"]}


def test_post_voices_uploads_a_new_sample(wiring):
    client, _tts_engine, _media_generator = wiring

    response = client.post("/voices", files={"file": ("second.wav", b"RIFF-fake-wav-bytes", "audio/wav")})

    assert response.status_code == 201
    assert response.json() == {"voices": ["narrator.wav", "second.wav"]}


def test_post_voices_returns_400_when_engine_does_not_support_upload(tmp_path):
    repository = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))
    use_case = ManageTaskQueueUseCase(repository=repository)
    tts_engine = FakeTTSEngine(upload_supported=False)
    media_generator = FakeMediaGenerator(tts_engine)
    manage_voices_use_case = ManageVoicesUseCase(tts_engine=tts_engine, media_generator=media_generator)
    app = create_app(use_case, manage_voices_use_case=manage_voices_use_case)
    client = TestClient(app)

    response = client.post("/voices", files={"file": ("second.wav", b"content", "audio/wav")})

    assert response.status_code == 400


def test_select_voice_returns_200_and_updates_the_active_voice(wiring):
    client, _tts_engine, media_generator = wiring

    response = client.post("/settings/voice", json={"voice": "narrator.wav"})

    assert response.status_code == 200
    assert media_generator.selected_voice == "narrator.wav"


def test_select_voice_returns_404_for_unknown_voice(wiring):
    client, _tts_engine, _media_generator = wiring

    response = client.post("/settings/voice", json={"voice": "missing.wav"})

    assert response.status_code == 404


def test_set_speed_returns_200_and_updates_the_speed(wiring):
    client, _tts_engine, media_generator = wiring

    response = client.post("/settings/speed", json={"speed": 1.5})

    assert response.status_code == 200
    assert media_generator.speech_speed == 1.5
