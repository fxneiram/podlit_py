import pytest

from application.ports.task_repository_port import TaskRepositoryPort
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase
from domain.exceptions import TaskNotFoundError
from domain.task_record import TaskRecord

VALID_TASK_TEXT = '{1: {"text": "Hello.", "language": "en"}, 2: {"text": "Hola.", "language": "es"}}'


class FakeTaskRepository(TaskRepositoryPort):
    def __init__(self):
        self._records: dict[str, TaskRecord] = {}
        self._next_id = 0

    def add(self, data):
        task_id = str(self._next_id)
        self._next_id += 1
        record = TaskRecord(id=task_id, data=data)
        self._records[task_id] = record
        return record

    def list_all(self):
        return list(self._records.values())

    def get(self, task_id):
        if task_id not in self._records:
            raise TaskNotFoundError(f"Task {task_id!r} not found")
        return self._records[task_id]

    def update(self, task_id, data):
        if task_id not in self._records:
            raise TaskNotFoundError(f"Task {task_id!r} not found")
        record = TaskRecord(id=task_id, data=data)
        self._records[task_id] = record
        return record

    def delete(self, task_id):
        if task_id not in self._records:
            raise TaskNotFoundError(f"Task {task_id!r} not found")
        del self._records[task_id]

    def replace_all(self, tasks_data):
        self._records = {}
        self._next_id = 0
        return [self.add(data) for data in tasks_data]


@pytest.fixture
def use_case():
    return ManageTaskQueueUseCase(repository=FakeTaskRepository())


def test_add_task_validates_and_stores(use_case):
    record = use_case.add_task(VALID_TASK_TEXT)

    assert record.id is not None
    assert record.data == {1: {"text": "Hello.", "language": "en"}, 2: {"text": "Hola.", "language": "es"}}


def test_add_task_raises_on_invalid_input(use_case):
    with pytest.raises(ValueError):
        use_case.add_task("not a valid dict at all {{{")


def test_list_tasks_returns_all_added(use_case):
    use_case.add_task(VALID_TASK_TEXT)
    use_case.add_task(VALID_TASK_TEXT)

    assert len(use_case.list_tasks()) == 2


def test_get_task_returns_matching_record(use_case):
    added = use_case.add_task(VALID_TASK_TEXT)

    fetched = use_case.get_task(added.id)

    assert fetched.id == added.id
    assert fetched.data == added.data


def test_get_task_raises_when_not_found(use_case):
    with pytest.raises(TaskNotFoundError):
        use_case.get_task("missing-id")


def test_update_task_validates_and_replaces_data(use_case):
    added = use_case.add_task(VALID_TASK_TEXT)
    new_text = '{1: {"text": "Updated.", "language": "en"}}'

    updated = use_case.update_task(added.id, new_text)

    assert updated.id == added.id
    assert updated.data == {1: {"text": "Updated.", "language": "en"}}


def test_update_task_raises_when_not_found(use_case):
    with pytest.raises(TaskNotFoundError):
        use_case.update_task("missing-id", VALID_TASK_TEXT)


def test_update_task_raises_on_invalid_input(use_case):
    added = use_case.add_task(VALID_TASK_TEXT)

    with pytest.raises(ValueError):
        use_case.update_task(added.id, "not valid {{{")


def test_delete_task_removes_it(use_case):
    added = use_case.add_task(VALID_TASK_TEXT)

    use_case.delete_task(added.id)

    assert use_case.list_tasks() == []


def test_delete_task_raises_when_not_found(use_case):
    with pytest.raises(TaskNotFoundError):
        use_case.delete_task("missing-id")


def test_get_queue_returns_all_tasks_in_order(use_case):
    first = use_case.add_task(VALID_TASK_TEXT)
    second = use_case.add_task(VALID_TASK_TEXT)

    queue = use_case.get_queue()

    assert [record.id for record in queue] == [first.id, second.id]


def test_replace_queue_discards_previous_tasks(use_case):
    use_case.add_task(VALID_TASK_TEXT)

    new_queue = use_case.replace_queue([VALID_TASK_TEXT, VALID_TASK_TEXT])

    assert len(new_queue) == 2
    assert len(use_case.list_tasks()) == 2


def test_replace_queue_raises_on_any_invalid_entry(use_case):
    with pytest.raises(ValueError):
        use_case.replace_queue([VALID_TASK_TEXT, "not valid {{{"])
