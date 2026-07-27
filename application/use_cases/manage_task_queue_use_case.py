from application.ports.task_repository_port import TaskRepositoryPort
from domain.task_record import TaskRecord
from models.task import Task


class ManageTaskQueueUseCase:
    """Orchestrates task queue CRUD: validates raw task text via Task.validate_input, then
    delegates storage to whatever TaskRepositoryPort implementation is injected. Previously
    this logic lived inline in WindowTaskQueueManager, mixing UI and business logic.
    """

    def __init__(self, repository: TaskRepositoryPort):
        self.repository = repository

    def add_task(self, raw_text: str) -> TaskRecord:
        data = Task.validate_input(raw_text)
        return self.repository.add(data)

    def list_tasks(self) -> list[TaskRecord]:
        return self.repository.list_all()

    def get_task(self, task_id: str) -> TaskRecord:
        return self.repository.get(task_id)

    def update_task(self, task_id: str, raw_text: str) -> TaskRecord:
        data = Task.validate_input(raw_text)
        return self.repository.update(task_id, data)

    def delete_task(self, task_id: str) -> None:
        self.repository.delete(task_id)

    def get_queue(self) -> list[TaskRecord]:
        return self.repository.list_all()

    def replace_queue(self, raw_texts: list[str]) -> list[TaskRecord]:
        validated = [Task.validate_input(text) for text in raw_texts]
        return self.repository.replace_all(validated)
