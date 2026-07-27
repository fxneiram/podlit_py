# REST API for task queue CRUD

Source: https://github.com/fxneiram/podlit_py/issues/15
Branch: feature/task-queue-rest-api

## Problem / goal

First issue of Épica A (Web UI): a real backend exposing the task queue as a REST API,
replacing `WindowTaskQueueManager`'s in-memory state and its pickle-based `.que` save/load with
JSON persistence. This is also a hard dependency for Épica B's endpoint issues (#23, #25 assume
an API server exists) — nothing in that epic can proceed until this lands.

## Design decisions (confirm before implementation)

**Framework: FastAPI + uvicorn, not Flask.** Verified compatible with this project's pinned
Python 3.9 stack (installed and imported alongside the full `requirements.txt` in a real
Python 3.9 venv — no conflicts, `pip check` clean). Reasoning: #16 (next issue) needs real-time
generation progress, which FastAPI supports natively (WebSockets/async) without an extra
extension the way Flask would need (`flask-socketio`). FastAPI's Pydantic-based request
validation and auto-generated OpenAPI docs are also useful for a personal project where testing
endpoints by hand matters.

**Fits the hexagonal-architecture target layout** (`hexagonal-architecture.md`) as a new
*driving* adapter, with a proper use-case layer this project didn't have yet:

```
application/
  ports/
    task_repository_port.py       TaskRepositoryPort (abstract) — get/list/add/update/delete/
                                   replace-all, matching what hexagonal-architecture.md already
                                   anticipated for this exact concern
  use_cases/
    manage_task_queue_use_case.py ManageTaskQueueUseCase — add_task/list_tasks/get_task/
                                   update_task/delete_task/get_queue/replace_queue, calling
                                   Task.validate_input for content validation and the port for
                                   storage. This is new: today this logic is inlined directly in
                                   WindowTaskQueueManager, mixing UI and business logic.
adapters/
  driven/persistence/
    json_task_repository.py       JsonTaskRepository(TaskRepositoryPort) — one JSON file on
                                   disk, path from pkg/config.py's new QUEUE_STORAGE_PATH
  driving/api/
    app.py                        FastAPI() app + route registration
    routes.py                     /tasks and /queue route handlers
    schemas.py                    Pydantic request/response models
domain/
  exceptions.py                   + TaskNotFoundError (404s)
```

`WindowTaskQueueManager` (Tkinter) is **not touched** — it keeps its own in-memory list and
pickle save/load exactly as today. This issue adds a second, independent way to manage a task
queue (the API, JSON-persisted); unifying the two or retiring Tkinter is #19's explicit job, not
this one's.

**Endpoint design** — "task" here means one full multi-row script (the
`{1: {text, language}, 2: {...}}` shape `Task.validate_input` already validates), matching
`CLAUDE.md`'s note that this is the actual unit the rest of the app calls a "task." The queue is
the ordered list of such tasks.

- `POST /tasks` — body: the raw `{index: {text, language}}` dict. Validated via
  `Task.validate_input`; a server-assigned UUID `id` is returned alongside the stored data.
- `GET /tasks` — list all tasks (each with its `id`).
- `GET /tasks/{id}` — fetch one.
- `PUT /tasks/{id}` — replace a task's content (re-validated the same way).
- `DELETE /tasks/{id}` — remove one.
- `GET /queue` — the full ordered queue (list of `{id, data}`), for future export (#19).
- `POST /queue` — bulk-replace the entire queue from a provided list, for future import (#19)
  and as the JSON-load equivalent of today's pickle-based "Load Queue" button.

**Task IDs**: server-assigned `uuid4` strings, not list position — stable across edits/deletes,
the standard REST pattern for addressable resources.

**Persistence**: one JSON file (`pkg/config.py`'s new `QUEUE_STORAGE_PATH`, default
`./queue_storage.json`), read/written by `JsonTaskRepository` on every mutation — simple and
matches the "queue persists across server restarts" acceptance criterion without needing a real
database for a single-user tool.

**New entry point**: `api_server.py` at the project root (parallel to `app.py`, which stays the
Tkinter entry point) wires `JsonTaskRepository` → `ManageTaskQueueUseCase` → the FastAPI app and
runs it via `uvicorn`. A `make run-api` target added alongside the existing `make run`.

**New dependencies** (verified installable/compatible on Python 3.9 above):
`fastapi==0.128.8`, `uvicorn==0.39.0`, `pydantic==2.13.4` in `requirements.txt`; `httpx==0.28.1`
in `requirements-dev.txt` only (needed for `TestClient`, not for running the server).

## Acceptance criteria

1. `application/ports/task_repository_port.py`, `application/use_cases/manage_task_queue_use_case.py`,
   `adapters/driven/persistence/json_task_repository.py`, `domain/exceptions.py::TaskNotFoundError`.
2. `adapters/driving/api/{app,routes,schemas}.py` implementing the six endpoints above.
3. `api_server.py` + `make run-api`.
4. Unit tests: `ManageTaskQueueUseCase` (mocked repository), `JsonTaskRepository` (real temp JSON
   file), each in isolation.
5. Integration tests: FastAPI `TestClient` driving the real app + real `JsonTaskRepository`
   against a temp file — full CRUD round-trip, validation-error responses, restart-persistence
   (write via one repository instance, read via a fresh one pointed at the same file).
6. `requirements.txt`/`requirements-dev.txt` updated with the new pins above.
7. `WindowTaskQueueManager`/`app.py` unchanged.

## Out of scope

#16 (real-time progress endpoint), #17 (voices API), #18/#19 (frontend, Tkinter retirement) —
all later issues in this epic. Épica B's endpoints (blocked on this issue, not built here).
