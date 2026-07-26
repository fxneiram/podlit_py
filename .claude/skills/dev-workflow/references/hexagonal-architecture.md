# Hexagonal architecture (ports & adapters) for podlit_py

podlit_py is migrating from its current flat layout (`fh/`, `models/`, `tk/`,
`audio_video_generator.py` all directly importing concrete libraries like `TTS.api` and
`tkinter`) to a hexagonal architecture. Read this whenever the implementation phase (step 5
of the dev-workflow) touches anything beyond a trivial, purely-cosmetic change.

## Why this matters here specifically

Today `AudioVideoGenerator` directly imports `TTS.api.TTS` and `torch`, and `fh/hvideo.py`
directly does the video rendering — which is exactly why unit tests for this project have to
mock library internals instead of swapping in a fake. Hexagonal architecture fixes that at the
root: the domain and application layers never import `TTS`, `torch`, `cv2`, or `tkinter`
directly — they only depend on ports (interfaces) that adapters implement. Once that's true,
unit tests use simple in-memory fakes instead of mocking third-party internals, and swapping
the TTS engine, the video backend, or the UI toolkit becomes a matter of writing a new adapter,
not touching business logic.

## The dependency rule

Dependencies only ever point inward:

```
adapters  --->  application  --->  domain
```

- **domain** knows nothing about the outside world — no imports of `TTS`, `torch`, `cv2`,
  `tkinter`, `json`, or the filesystem. Pure Python data + business rules.
- **application** orchestrates domain objects to fulfill use cases, talking to the outside
  world only through **ports** (abstract interfaces) that it defines. It does not know which
  concrete adapter is plugged in.
- **adapters** implement ports (driven/secondary adapters: TTS engine, video renderer, audio
  processor, file/task persistence) or drive the application (driving/primary adapters: the
  Tkinter UI, and later a CLI if one ever exists). Adapters may import third-party libraries
  freely — that's their entire job.

If you ever need `application/` or `domain/` to import from `adapters/`, that's a sign the
port is missing or wrong — fix the port, don't add the import.

## Target package layout

```
domain/
  task.py                    Task (was models/task.py) — pure business rules, no JSON/file I/O
  row.py                     Row (was models/row.py)
  exceptions.py              Domain-specific errors (e.g. InvalidRowError)

application/
  ports/
    tts_port.py               TextToSpeechPort — synthesize(text, language, voice, speed) -> audio bytes/path
    video_renderer_port.py     VideoRendererPort — render_fragment(audio_path, text) -> video_path
    audio_processor_port.py    AudioProcessorPort — add_silence(audio_path, ms, ...), and similar
    file_storage_port.py       FileStoragePort — temp/output path management, work folder creation
    task_repository_port.py    TaskRepositoryPort — load_queue(), save_queue(tasks), by-name lookup
  use_cases/
    generate_media_use_case.py     GenerateMediaUseCase — replaces the orchestration currently
                                    inline in audio_video_generator.py: iterate a Task's Rows,
                                    call TextToSpeechPort + AudioProcessorPort + VideoRendererPort,
                                    hand off to FileStoragePort for the final concatenated output
    manage_task_queue_use_case.py  AddTask/EditTask/RemoveTask/ReorderTask/SaveQueue/LoadQueue —
                                    currently scattered across tk/window_task_queue_manager.py

adapters/
  driven/                      "secondary" adapters — implement application/ports/*
    tts/
      coqui_tts_adapter.py       implements TextToSpeechPort using TTS.api.TTS (+ device/cuda selection)
    video/
      opencv_video_adapter.py    implements VideoRendererPort (current fh/hvideo.py logic)
    audio/
      pydub_audio_adapter.py     implements AudioProcessorPort (current fh/haudio.py logic)
    persistence/
      json_task_repository.py   implements TaskRepositoryPort (task queue load/save as JSON)
    filesystem/
      local_file_storage_adapter.py  implements FileStoragePort (current fh/hfiles.py logic)
  driving/                     "primary" adapters — call INTO application/use_cases/*
    ui_tkinter/
      window_task_queue_manager.py   (moved from tk/) calls ManageTaskQueueUseCase / GenerateMediaUseCase
      treeview_task_queue.py         (moved from tk/) — pure widget, unchanged

config/
  settings.py                 (renamed from pkg/config.py) — paths, colors, sizes, FPS constants;
                               adapters read from here, domain/application never do

app.py                        Composition root: builds concrete adapters, injects them into the
                               use cases, wires the use cases into the driving adapter (Tkinter),
                               and starts it. This is the ONLY file allowed to know about every
                               concrete adapter at once.
```

## Naming conventions

- Ports: abstract classes or `typing.Protocol` in `application/ports/`, suffix `Port`
  (`TextToSpeechPort`, not `ITts` or `TtsInterface`).
- Adapters: suffix `Adapter`, named after the concrete technology (`CoquiTTSAdapter`,
  `JSONTaskRepository` is acceptable too — pick one convention and keep it consistent across
  `adapters/driven/`).
- Use cases: suffix `UseCase`, named as a verb phrase (`GenerateMediaUseCase`, not
  `MediaService` or `MediaManager`) — a use case is one thing the application does, not a bag
  of related methods.

## Migration strategy — incremental, not a big-bang rewrite

Retrofitting hexagonal architecture onto an existing codebase is itself a large change, and
step 5 of the main workflow already requires small, well-described commits — don't turn "add
one feature" into "also rewrite the whole architecture" in a single PR. Instead, apply the
strangler pattern:

1. When a dev-workflow run touches a module that still lives in the old flat layout, migrate
   *only the piece it touches* into the new structure as part of that change (e.g. fixing a bug
   in `fh/haudio.py` is the moment to introduce `AudioProcessorPort` +
   `PydubAudioAdapter`, moving just that logic — not `fh/hvideo.py` too).
   Do this as its own early commit in the sequence (see step 5's commit-planning guidance),
   separate from the actual feature/fix commits.
2. Never leave a port half-implemented — if you introduce `TextToSpeechPort`, the concrete
   `CoquiTTSAdapter` must fully implement it in the same change; don't add an interface with
   no real implementation behind it.
3. Update `app.py` (the composition root) in the same commit that finishes moving a piece,
   so the app never has a module simultaneously wired the old way and the new way.
4. Prefer creating a new use case/port over expanding an existing one when a fix is
   tangential — a `GenerateMediaUseCase` gaining an unrelated queue-management method is a
   sign it should have been `ManageTaskQueueUseCase` instead.
5. It's fine for old and new structure to coexist for a while during the migration — track
   what's left to migrate in the spec's "Out of scope" section (see
   [spec-template.md](spec-template.md)) so it isn't silently forgotten, rather than pretending
   the migration is finished before it is.

## Testing implications

Once ports exist, unit tests (step 4 of the workflow) inject fakes that implement the port
directly instead of mocking library internals:

```python
class FakeTTSAdapter(TextToSpeechPort):
    def synthesize(self, text, language, voice, speed):
        return "fake_audio.wav"
```

This is strictly better than `unittest.mock.patch("TTS.api.TTS")` — it's typed, it can't drift
silently from the real adapter's signature, and it makes the use case's test read as "given
this port behavior, the use case does X" rather than "given this mock call sequence...".
Integration tests (step 6) should exercise at least one use case wired to its *real* driven
adapters (except the genuinely expensive ones — TTS model inference, GPU calls), to confirm the
wiring itself, not just each side in isolation.
