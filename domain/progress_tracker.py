from dataclasses import dataclass


@dataclass
class ProgressState:
    status: str  # "idle" | "running" | "completed"
    queue_progress: float = 0.0  # 0-100, overall
    current_task_index: int | None = None
    current_task_progress: float = 0.0  # 0-100, current task only
    current_task_status: str = ""


class ProgressTracker:
    """In-memory progress state for the (single) task queue this app processes - matches
    Tkinter's task_progress/queue_progress. One instance per running server; a restart mid-
    processing loses progress state, same as the current Tkinter app losing it on close.
    """

    def __init__(self):
        self._state = ProgressState(status="idle")

    @property
    def state(self) -> ProgressState:
        return self._state

    def start(self) -> None:
        self._state = ProgressState(status="running")

    def update_current_task(self, task_index: int, total_tasks: int, task_progress: float, status: str) -> None:
        queue_progress = round((task_index + task_progress / 100) / total_tasks * 100, 2)
        self._state = ProgressState(
            status="running",
            queue_progress=queue_progress,
            current_task_index=task_index,
            current_task_progress=task_progress,
            current_task_status=status,
        )

    def complete(self) -> None:
        self._state = ProgressState(status="completed", queue_progress=100.0)
