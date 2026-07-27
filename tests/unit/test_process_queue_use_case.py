import threading

import pytest

from application.ports.task_repository_port import TaskRepositoryPort
from application.use_cases.process_queue_use_case import ProcessQueueUseCase
from domain.exceptions import QueueAlreadyProcessingError
from domain.progress_tracker import ProgressTracker
from domain.task_record import TaskRecord


class FakeTaskRepository(TaskRepositoryPort):
    def __init__(self, records):
        self._records = records

    def add(self, data):
        raise NotImplementedError

    def list_all(self):
        return self._records

    def get(self, task_id):
        raise NotImplementedError

    def update(self, task_id, data):
        raise NotImplementedError

    def delete(self, task_id):
        raise NotImplementedError

    def replace_all(self, tasks_data):
        raise NotImplementedError


class FakeMediaGenerator:
    def __init__(self):
        self.generate_files_calls = []
        self.combine_queue_calls = []

    def generate_files(self, text_to_speak, progress_callback):
        progress_callback(50, "Processing fragment 1/2")
        progress_callback(100, "Done")
        self.generate_files_calls.append(text_to_speak)
        index = len(self.generate_files_calls)
        return f"/output/{index}.wav", f"/output/{index}.mp4"

    def combine_queue(self, tasks, file_name=""):
        self.combine_queue_calls.append((tasks, file_name))


@pytest.fixture
def two_task_repository():
    return FakeTaskRepository(
        [
            TaskRecord(id="a", data={1: {"text": "Hello.", "language": "en"}}),
            TaskRecord(id="b", data={1: {"text": "Hola.", "language": "es"}}),
        ]
    )


def test_start_processes_every_task_in_the_repository(two_task_repository):
    media_generator = FakeMediaGenerator()
    use_case = ProcessQueueUseCase(two_task_repository, media_generator, ProgressTracker())

    use_case.start()
    use_case.wait_until_done(timeout=5)

    assert len(media_generator.generate_files_calls) == 2


def test_start_updates_progress_tracker_to_completed(two_task_repository):
    use_case = ProcessQueueUseCase(two_task_repository, FakeMediaGenerator(), (tracker := ProgressTracker()))

    use_case.start()
    use_case.wait_until_done(timeout=5)

    assert tracker.state.status == "completed"
    assert tracker.state.queue_progress == 100.0


class BlockingMediaGenerator:
    """generate_files blocks until release() is called, so the background thread is
    guaranteed to still be alive when the test checks is_running()/start()."""

    def __init__(self):
        self._release = threading.Event()
        self.entered = threading.Event()

    def release(self):
        self._release.set()

    def generate_files(self, text_to_speak, progress_callback):
        self.entered.set()
        self._release.wait(timeout=5)
        return "/output/1.wav", "/output/1.mp4"

    def combine_queue(self, tasks, file_name=""):
        pass


def test_start_raises_if_already_running(two_task_repository):
    media_generator = BlockingMediaGenerator()
    use_case = ProcessQueueUseCase(two_task_repository, media_generator, ProgressTracker())
    use_case.start()
    media_generator.entered.wait(timeout=5)

    with pytest.raises(QueueAlreadyProcessingError):
        use_case.start()

    media_generator.release()
    use_case.wait_until_done(timeout=5)


def test_mix_queue_true_combines_generated_outputs(two_task_repository):
    media_generator = FakeMediaGenerator()
    use_case = ProcessQueueUseCase(two_task_repository, media_generator, ProgressTracker())

    use_case.start(mix_queue=True)
    use_case.wait_until_done(timeout=5)

    assert len(media_generator.combine_queue_calls) == 1


def test_mix_queue_false_does_not_combine(two_task_repository):
    media_generator = FakeMediaGenerator()
    use_case = ProcessQueueUseCase(two_task_repository, media_generator, ProgressTracker())

    use_case.start(mix_queue=False)
    use_case.wait_until_done(timeout=5)

    assert media_generator.combine_queue_calls == []


def test_empty_queue_completes_immediately_without_calling_generate_files():
    empty_repository = FakeTaskRepository([])
    media_generator = FakeMediaGenerator()
    use_case = ProcessQueueUseCase(empty_repository, media_generator, (tracker := ProgressTracker()))

    use_case.start()
    use_case.wait_until_done(timeout=5)

    assert media_generator.generate_files_calls == []
    assert tracker.state.status == "completed"


def test_is_running_reflects_thread_state(two_task_repository):
    use_case = ProcessQueueUseCase(two_task_repository, FakeMediaGenerator(), ProgressTracker())

    assert use_case.is_running() is False

    use_case.start()
    use_case.wait_until_done(timeout=5)

    assert use_case.is_running() is False
