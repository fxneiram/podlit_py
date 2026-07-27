# Endpoint to process the queue with real-time progress

Source: https://github.com/fxneiram/podlit_py/issues/16
Branch: feature/queue-processing-progress-endpoint

## Problem / goal

Second issue of Épica A, building directly on #15's REST API. Expose
`AudioVideoGenerator.generate_files`/`combine_queue` (today only reachable from
`WindowTaskQueueManager`'s `progress_callback`-driven Tkinter flow) as an API operation, with
real-time progress the frontend can display without aggressive polling.

## Design decisions (confirm before implementation)

**Server-Sent Events (SSE), not WebSocket.** The data flow here is one-directional
(server → client progress pushes); nothing in this issue's scope needs the client to send
messages back over the same channel during generation. SSE is simpler to implement (a plain
`StreamingResponse` with `media_type="text/event-stream"`, no extra dependency) and is the
standard fit for "push updates, no client-to-server chatter" — matches the acceptance criterion
("sin hacer polling agresivo") without WebSocket's added complexity.

**Background execution: a dedicated thread, mirroring the existing Tkinter pattern.**
`WindowTaskQueueManager.process_next_task` already runs each task in its own
`threading.Thread`, polls completion, and applies `task_delay` between tasks via
`root.after`. The API version keeps the same shape — a single background thread iterates the
queue, calls `generate_files` per task, sleeps `task_delay_ms` between tasks — rather than
using FastAPI's `BackgroundTasks` (which runs on the request's own worker and isn't a good fit
for a queue that can run far longer than any reasonable request timeout) or introducing a task
queue system (Celery etc. — real overkill for a single-user local tool).

**"Shutdown on complete" is out of scope for this endpoint.** The existing Tkinter feature
(`shutdown_after_completion`, `os.system("shutdown /s /f /t 1")`) shuts down the *desktop
machine* when a queue finishes — that doesn't translate sensibly to a web API that might be
long-running on a shared or remote machine. Not porting it; flagging here so it isn't silently
forgotten if a future issue wants an equivalent ("stop the server"?) concept.

**Progress data model** — one in-memory `ProgressTracker` (matches `task_progress`/
`queue_progress` in the Tkinter code):
```python
status: Literal["idle", "running", "completed"]
queue_progress: float          # 0-100, overall
current_task_index: int | None
current_task_progress: float   # 0-100, current task only
current_task_status: str       # e.g. "Processing fragment 2/5"
```
Single in-memory instance (this app has exactly one queue and one user) — no per-job ids, no
persistence; a server restart mid-processing loses progress state (acceptable for this issue's
scope, matching how the current Tkinter version doesn't survive an app restart either).

## Endpoints

- `POST /queue/process` — body: `{"task_delay_ms": 0, "mix_queue": false}`. Starts the
  background thread (returns `409` if already running), processes every task currently in the
  repository via `AudioVideoGenerator.generate_files`, applying `task_delay_ms` between tasks;
  if `mix_queue` is true, calls `combine_queue` on the generated outputs once the loop
  finishes. Returns `202` immediately.
- `GET /queue/progress` — SSE stream of `ProgressTracker` state, one event whenever it
  changes (polled internally at a short interval, not exposed as client-side polling).

## Acceptance criteria

1. `application/use_cases/process_queue_use_case.py`: `ProcessQueueUseCase` — background
   thread, per-task + queue progress via `ProgressTracker`, `task_delay_ms`, `mix_queue`.
2. `domain/progress_tracker.py` (or similar): the state model above.
3. `adapters/driving/api/routes.py` (or a new `queue_routes.py`): `POST /queue/process`,
   `GET /queue/progress` (SSE).
4. `api_server.py` wires `AudioVideoGenerator` (via `app.py`'s existing `build_tts_engine`) and
   `ProcessQueueUseCase` into the app alongside #15's existing pieces.
5. Tests: `ProcessQueueUseCase` unit tests with a fake `TextToSpeechPort`/`AudioVideoGenerator`
   double (per this project's established "don't touch real TTS/audio in tests" pattern) and a
   fake repository; integration test driving `POST /queue/process` then reading the SSE stream
   via `TestClient`, asserting progress reaches `"completed"`.
6. `WindowTaskQueueManager`/`app.py`'s Tkinter flow unchanged.

## Out of scope

Shutdown-on-complete (see above). #17 (voices API), #18/#19 (frontend, Tkinter retirement).
