"""Real FastAPI TestClient + real JsonTaskRepository against a temp file - only the actual
network socket is stubbed by TestClient, which is the standard way to test a FastAPI app.
Matches this project's "don't mock what's cheap and real" testing philosophy.
"""

import pytest
from fastapi.testclient import TestClient

from adapters.driven.persistence.json_task_repository import JsonTaskRepository
from adapters.driving.api.app import create_app
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase

VALID_TASK_TEXT = '{1: {"text": "Hello.", "language": "en"}}'


@pytest.fixture
def client(tmp_path):
    repository = JsonTaskRepository(storage_path=str(tmp_path / "queue.json"))
    use_case = ManageTaskQueueUseCase(repository=repository)
    app = create_app(use_case)
    return TestClient(app)


def test_create_task_returns_201_with_id_and_validated_data(client):
    response = client.post("/tasks", json={"raw_text": VALID_TASK_TEXT})

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["data"] == {"1": {"text": "Hello.", "language": "en"}}


def test_create_task_returns_400_on_invalid_input(client):
    response = client.post("/tasks", json={"raw_text": "not valid {{{"})

    assert response.status_code == 400


def test_full_crud_round_trip(client):
    create_response = client.post("/tasks", json={"raw_text": VALID_TASK_TEXT})
    task_id = create_response.json()["id"]

    list_response = client.get("/tasks")
    assert len(list_response.json()) == 1

    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == task_id

    new_text = '{1: {"text": "Updated.", "language": "en"}}'
    update_response = client.put(f"/tasks/{task_id}", json={"raw_text": new_text})
    assert update_response.status_code == 200
    assert update_response.json()["data"]["1"]["text"] == "Updated."

    delete_response = client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 204

    assert client.get("/tasks").json() == []


def test_get_task_returns_404_for_unknown_id(client):
    response = client.get("/tasks/does-not-exist")

    assert response.status_code == 404


def test_update_task_returns_404_for_unknown_id(client):
    response = client.put("/tasks/does-not-exist", json={"raw_text": VALID_TASK_TEXT})

    assert response.status_code == 404


def test_delete_task_returns_404_for_unknown_id(client):
    response = client.delete("/tasks/does-not-exist")

    assert response.status_code == 404


def test_queue_endpoints_mirror_tasks(client):
    client.post("/tasks", json={"raw_text": VALID_TASK_TEXT})

    queue_response = client.get("/queue")

    assert len(queue_response.json()) == 1


def test_replace_queue_bulk_creates_tasks(client):
    client.post("/tasks", json={"raw_text": VALID_TASK_TEXT})

    response = client.post("/queue", json={"raw_texts": [VALID_TASK_TEXT, VALID_TASK_TEXT]})

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert len(client.get("/tasks").json()) == 2


def test_queue_persists_across_a_fresh_app_instance(tmp_path):
    """The actual acceptance criterion: the queue survives a server restart."""
    storage_path = str(tmp_path / "queue.json")

    first_use_case = ManageTaskQueueUseCase(repository=JsonTaskRepository(storage_path=storage_path))
    first_client = TestClient(create_app(first_use_case))
    created = first_client.post("/tasks", json={"raw_text": VALID_TASK_TEXT}).json()

    second_use_case = ManageTaskQueueUseCase(repository=JsonTaskRepository(storage_path=storage_path))
    second_client = TestClient(create_app(second_use_case))

    response = second_client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
