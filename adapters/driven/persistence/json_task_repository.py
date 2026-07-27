import json
import os
import uuid
from typing import Any

from application.ports.task_repository_port import TaskRepositoryPort
from domain.exceptions import TaskNotFoundError
from domain.task_record import TaskRecord


class JsonTaskRepository(TaskRepositoryPort):
    """Stores the task queue as a single JSON file on disk - simple and enough for this
    single-user tool, no database needed. Note: JSON object keys are always strings, so a
    task's originally-int keys (from Task.validate_input) come back as strings after being
    read from a fresh instance - the generation pipeline only ever iterates .items() without
    caring about key type, so this is harmless in practice.
    """

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            self._write([])

    def add(self, data: dict) -> TaskRecord:
        records = self._read()
        task_id = str(uuid.uuid4())
        records.append({"id": task_id, "data": data})
        self._write(records)
        return TaskRecord(id=task_id, data=data)

    def list_all(self) -> list[TaskRecord]:
        return [TaskRecord(id=r["id"], data=r["data"]) for r in self._read()]

    def get(self, task_id: str) -> TaskRecord:
        for r in self._read():
            if r["id"] == task_id:
                return TaskRecord(id=r["id"], data=r["data"])
        raise TaskNotFoundError(f"Task {task_id!r} not found")

    def update(self, task_id: str, data: dict) -> TaskRecord:
        records = self._read()
        for r in records:
            if r["id"] == task_id:
                r["data"] = data
                self._write(records)
                return TaskRecord(id=task_id, data=data)
        raise TaskNotFoundError(f"Task {task_id!r} not found")

    def delete(self, task_id: str) -> None:
        records = self._read()
        filtered = [r for r in records if r["id"] != task_id]
        if len(filtered) == len(records):
            raise TaskNotFoundError(f"Task {task_id!r} not found")
        self._write(filtered)

    def replace_all(self, tasks_data: list[dict]) -> list[TaskRecord]:
        records: list[dict[str, Any]] = [{"id": str(uuid.uuid4()), "data": data} for data in tasks_data]
        self._write(records)
        return [TaskRecord(id=r["id"], data=r["data"]) for r in records]

    def _read(self) -> list[dict[str, Any]]:
        with open(self.storage_path) as f:
            return json.load(f)

    def _write(self, records: list[dict[str, Any]]) -> None:
        with open(self.storage_path, "w") as f:
            json.dump(records, f, indent=2)
