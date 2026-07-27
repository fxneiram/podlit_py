from abc import ABC, abstractmethod

from domain.task_record import TaskRecord


class TaskRepositoryPort(ABC):
    """Contract for storing/retrieving the task queue. Concrete adapters decide how (JSON
    file, database, in-memory) - callers only depend on this interface.
    """

    @abstractmethod
    def add(self, data: dict) -> TaskRecord:
        """Store a new task, assigning it an id, and return the resulting record."""

    @abstractmethod
    def list_all(self) -> list[TaskRecord]:
        """Return every stored task, in queue order."""

    @abstractmethod
    def get(self, task_id: str) -> TaskRecord:
        """Return one task by id.

        Raises:
            TaskNotFoundError: if `task_id` doesn't exist.
        """

    @abstractmethod
    def update(self, task_id: str, data: dict) -> TaskRecord:
        """Replace an existing task's data, keeping its id.

        Raises:
            TaskNotFoundError: if `task_id` doesn't exist.
        """

    @abstractmethod
    def delete(self, task_id: str) -> None:
        """Remove a task by id.

        Raises:
            TaskNotFoundError: if `task_id` doesn't exist.
        """

    @abstractmethod
    def replace_all(self, tasks_data: list[dict]) -> list[TaskRecord]:
        """Replace the entire queue with new tasks (fresh ids), in the given order."""
