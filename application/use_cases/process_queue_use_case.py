import threading
import time
from typing import Any, Optional, Protocol

from application.ports.task_repository_port import TaskRepositoryPort
from domain.exceptions import QueueAlreadyProcessingError
from domain.progress_tracker import ProgressTracker


class MediaGenerator(Protocol):
    """Structural contract for the collaborator that turns one task's data into output
    files - matches AudioVideoGenerator's public shape without requiring inheritance from it,
    so tests can supply a lightweight fake."""

    def generate_files(self, text_to_speak: dict, progress_callback: Any) -> tuple[str, str]: ...

    def combine_queue(self, processed_tasks: list, file_name: str = "") -> None: ...


class ProcessQueueUseCase:
    """Processes every task currently in the repository on a background thread, mirroring
    WindowTaskQueueManager.process_next_task's threading/delay/mix_queue behavior for the API."""

    def __init__(
        self, repository: TaskRepositoryPort, media_generator: MediaGenerator, progress_tracker: ProgressTracker
    ):
        self._repository = repository
        self._media_generator = media_generator
        self._progress_tracker = progress_tracker
        self._thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, task_delay_ms: int = 0, mix_queue: bool = False) -> None:
        if self.is_running():
            raise QueueAlreadyProcessingError("Queue processing is already running")

        self._progress_tracker.start()
        self._thread = threading.Thread(target=self._run, args=(task_delay_ms, mix_queue), daemon=True)
        self._thread.start()

    def wait_until_done(self, timeout: Optional[float] = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _run(self, task_delay_ms: int, mix_queue: bool) -> None:
        records = self._repository.list_all()
        total_tasks = len(records)
        processed_outputs = []

        for index, record in enumerate(records):

            def progress_callback(progress: float, status: str = "Processing", index: int = index) -> None:
                self._progress_tracker.update_current_task(index, total_tasks, progress, status)

            output_files = self._media_generator.generate_files(record.data, progress_callback)
            processed_outputs.append(output_files)

            if task_delay_ms and index < total_tasks - 1:
                time.sleep(task_delay_ms / 1000)

        if mix_queue and processed_outputs:
            self._media_generator.combine_queue(processed_outputs)

        self._progress_tracker.complete()
