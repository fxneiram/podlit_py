"""Real FastAPI TestClient driving POST /queue/process and reading the GET /queue/progress SSE
stream - only the media generator is faked (per this project's "don't touch real TTS/audio in
tests" pattern); the repository, use case, and HTTP layer are all real.
"""

import json
import threading

import pytest
from fastapi.testclient import TestClient

from adapters.driven.persistence.json_task_repository import JsonTaskRepository
from adapters.driving.api.app import create_app
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase
from application.use_cases.process_queue_use_case import ProcessQueueUseCase
from domain.progress_tracker import ProgressTracker

VALID_TASK_TEXT = '{1: {"text": "Hello.", "language": "en"}}'


class FakeMediaGenerator:
    def __init__(self):
        self.generate_files_calls = []
        self.combine_queue_calls = []

    def generate_files(self, text_to_speak, progress_callback):
        progress_callback(100, "Done")
        self.generate_files_calls.append(text_to_speak)
        return "/output/1.wav", "/output/1.mp4"

    def combine_queue(self, tasks, file_name=""):
        self.combine_queue_calls.append((tasks, file_name))


@pytest.fixture
def wiring(tmp_path):
    repository = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))
    use_case = ManageTaskQueueUseCase(repository=repository)
    media_generator = FakeMediaGenerator()
    progress_tracker = ProgressTracker()
    process_queue_use_case = ProcessQueueUseCase(
        repository=repository, media_generator=media_generator, progress_tracker=progress_tracker
    )
    app = create_app(use_case, process_queue_use_case=process_queue_use_case, progress_tracker=progress_tracker)
    return TestClient(app), use_case, media_generator, process_queue_use_case


def _read_sse_events(response):
    events = []
    for line in response.iter_lines():
        if line and line.startswith("data: "):
            events.append(json.loads(line[len("data: ") :]))
    return events


def test_process_queue_returns_202_and_processes_every_task(wiring):
    client, use_case, media_generator, process_queue_use_case = wiring
    use_case.add_task(VALID_TASK_TEXT)
    use_case.add_task(VALID_TASK_TEXT)

    response = client.post("/queue/process", json={})

    assert response.status_code == 202
    process_queue_use_case.wait_until_done(timeout=5)
    assert len(media_generator.generate_files_calls) == 2


def test_process_queue_returns_409_when_already_running(tmp_path):
    repository = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))
    use_case = ManageTaskQueueUseCase(repository=repository)
    use_case.add_task(VALID_TASK_TEXT)

    release = threading.Event()
    entered = threading.Event()

    class BlockingMediaGenerator:
        def generate_files(self, text_to_speak, progress_callback):
            entered.set()
            release.wait(timeout=5)
            return "/output/1.wav", "/output/1.mp4"

        def combine_queue(self, tasks, file_name=""):
            pass

    progress_tracker = ProgressTracker()
    process_queue_use_case = ProcessQueueUseCase(
        repository=repository, media_generator=BlockingMediaGenerator(), progress_tracker=progress_tracker
    )
    app = create_app(use_case, process_queue_use_case=process_queue_use_case, progress_tracker=progress_tracker)
    client = TestClient(app)

    client.post("/queue/process", json={})
    entered.wait(timeout=5)

    response = client.post("/queue/process", json={})

    assert response.status_code == 409
    release.set()
    process_queue_use_case.wait_until_done(timeout=5)


def test_process_queue_with_mix_queue_combines_outputs(wiring):
    client, use_case, media_generator, process_queue_use_case = wiring
    use_case.add_task(VALID_TASK_TEXT)

    client.post("/queue/process", json={"mix_queue": True})
    process_queue_use_case.wait_until_done(timeout=5)

    assert len(media_generator.combine_queue_calls) == 1


def test_progress_stream_reaches_completed(wiring):
    client, use_case, _media_generator, process_queue_use_case = wiring
    use_case.add_task(VALID_TASK_TEXT)
    client.post("/queue/process", json={})
    process_queue_use_case.wait_until_done(timeout=5)

    with client.stream("GET", "/queue/progress") as response:
        events = _read_sse_events(response)

    assert events
    assert events[-1]["status"] == "completed"
    assert events[-1]["queue_progress"] == 100.0
