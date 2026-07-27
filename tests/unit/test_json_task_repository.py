import json

import pytest

from adapters.driven.persistence.json_task_repository import JsonTaskRepository
from domain.exceptions import TaskNotFoundError

TASK_DATA = {1: {"text": "Hello.", "language": "en"}}


def _after_json_round_trip(data: dict) -> dict:
    """`get`/`list_all` always re-read from disk, and JSON object keys are always strings -
    so any int keys in `data` come back as strings, even from the same repository instance
    that just wrote them. Used to compute what a comparison should expect after a read."""
    return json.loads(json.dumps(data))


def test_add_assigns_an_id_and_persists(tmp_path):
    repo = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))

    record = repo.add(TASK_DATA)

    assert record.id
    assert record.data == TASK_DATA


def test_list_all_returns_added_tasks_in_order(tmp_path):
    repo = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))
    first = repo.add(TASK_DATA)
    second = repo.add({1: {"text": "Second.", "language": "en"}})

    records = repo.list_all()

    assert [r.id for r in records] == [first.id, second.id]


def test_get_returns_matching_record(tmp_path):
    repo = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))
    added = repo.add(TASK_DATA)

    fetched = repo.get(added.id)

    assert fetched.id == added.id


def test_get_raises_when_not_found(tmp_path):
    repo = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))

    with pytest.raises(TaskNotFoundError):
        repo.get("missing-id")


def test_update_replaces_data_keeping_id(tmp_path):
    repo = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))
    added = repo.add(TASK_DATA)
    new_data = {1: {"text": "Updated.", "language": "en"}}

    updated = repo.update(added.id, new_data)

    assert updated.id == added.id
    assert repo.get(added.id).data == _after_json_round_trip(new_data)


def test_update_raises_when_not_found(tmp_path):
    repo = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))

    with pytest.raises(TaskNotFoundError):
        repo.update("missing-id", TASK_DATA)


def test_delete_removes_the_task(tmp_path):
    repo = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))
    added = repo.add(TASK_DATA)

    repo.delete(added.id)

    assert repo.list_all() == []


def test_delete_raises_when_not_found(tmp_path):
    repo = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))

    with pytest.raises(TaskNotFoundError):
        repo.delete("missing-id")


def test_replace_all_discards_previous_tasks_with_fresh_ids(tmp_path):
    repo = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))
    original = repo.add(TASK_DATA)

    new_records = repo.replace_all([TASK_DATA, TASK_DATA])

    assert len(new_records) == 2
    assert all(r.id != original.id for r in new_records)
    assert len(repo.list_all()) == 2


def test_data_persists_across_repository_instances(tmp_path):
    """The whole point of JSON persistence: a fresh JsonTaskRepository instance pointed at
    the same file (simulating a server restart) can read what a previous instance wrote."""
    storage_path = str(tmp_path / "queue.json")
    first_instance = JsonTaskRepository(storage_path=storage_path)
    added = first_instance.add(TASK_DATA)

    second_instance = JsonTaskRepository(storage_path=storage_path)

    assert second_instance.get(added.id).data == _after_json_round_trip(TASK_DATA)


def test_integer_keys_become_strings_after_a_json_round_trip(tmp_path):
    """Documented, not a bug: Task.validate_input produces int keys (matching the Python-
    literal syntax ChatGPT output uses), but JSON object keys are always strings - a fresh
    repository instance reading the same file back sees string keys. The generation pipeline
    (AudioVideoGenerator.generate_files) only ever iterates .items() without caring about key
    type, so this is harmless in practice, but worth making explicit here."""
    storage_path = str(tmp_path / "queue.json")
    first_instance = JsonTaskRepository(storage_path=storage_path)
    added = first_instance.add(TASK_DATA)
    assert list(added.data.keys()) == [1]

    second_instance = JsonTaskRepository(storage_path=storage_path)

    assert list(second_instance.get(added.id).data.keys()) == ["1"]
