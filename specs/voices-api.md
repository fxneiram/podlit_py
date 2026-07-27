# Voice management via API

Source: https://github.com/fxneiram/podlit_py/issues/17
Branch: feature/voices-api

## Problem / goal

Third issue of Épica A, building on #15/#16. Expose what `AudioVideoGenerator.load_voices` /
`change_voice` / `set_speech_speed` already do (today only reachable from the Tkinter UI) as API
operations, plus a new capability the Tkinter UI never had: uploading a new voice sample without
touching the filesystem manually.

## Design decisions

**Voice upload is a `TextToSpeechPort` capability, not assumed for every engine.** The issue
itself flags that a future TTS engine may not support voice-cloning-style sample uploads (only
XTTS v2/Coqui does, among the four adapters that exist today). Mirrors the existing
`supports_ssml()` / `SSMLNotSupportedError` pattern already on the port:
- `TextToSpeechPort.supports_voice_upload() -> bool` (abstract, every adapter implements it)
- `TextToSpeechPort.add_voice(filename: str, content: bytes) -> None` (abstract; raises
  `VoiceUploadNotSupportedError` if `supports_voice_upload()` is `False`)
- `CoquiTTSAdapter`: `supports_voice_upload` → `True`; `add_voice` writes `content` to
  `voices_dir` under `os.path.basename(filename)` (path-traversal-safe — an uploaded filename
  like `../../etc/passwd` must not escape `voices_dir`), requires a `.wav` extension (XTTS
  speaker-reference format), and refreshes the cached voice list.
- `EspeakNGAdapter`, `MaryTTSAdapter`, `MagpieTTSAdapter`: `supports_voice_upload` → `False`;
  `add_voice` raises `VoiceUploadNotSupportedError`.

**Voice selection / speed stay on the existing `AudioVideoGenerator` instance**, the same one
`ProcessQueueUseCase` already holds (from #16) — `selected_voice`/`speech_speed` are read by
`generate_files` per task, so there's exactly one source of truth, no new state to keep in sync.
The new use case depends on a small structurally-typed `VoiceSettingsManager` (matches
`AudioVideoGenerator.load_voices`/`change_voice`/`set_speech_speed`), the same `Protocol`-based
pattern `ProcessQueueUseCase` used for its media generator dependency in #16 - keeps tests fast
with a fake double instead of a real `AudioVideoGenerator`.

**`POST /settings/voice` validates against the live voice list** (`VoiceNotFoundError` → 404) -
an API boundary is exactly where CLAUDE.md's "validate at system boundaries" applies, unlike
`AudioVideoGenerator.change_voice` today which sets `selected_voice` with no validation at all
(that's existing Tkinter-flow behavior, left untouched). `POST /settings/speed` does **not**
add new validation - `set_speech_speed` already clamps silently to `[0.1, 3.0]`, matching
existing behavior.

**New dependency**: `python-multipart==0.0.20`, required at runtime by FastAPI's
`UploadFile`/`File(...)` — added to `requirements.txt` (not just `-dev`), verified installing
cleanly in the real Python 3.9 venv alongside the existing pins (`pip check` clean, only the
pre-existing unrelated `grpcio` platform warning).

## Endpoints

- `GET /voices` — `{"voices": [...]}`, the engine's current voice catalog.
- `POST /voices` — multipart file upload (`file: UploadFile`). `201` with the updated voice
  list on success; `400` if the active engine doesn't support voice upload
  (`VoiceUploadNotSupportedError`) or the file isn't a `.wav`.
- `POST /settings/voice` — body `{"voice": "..."}`. `200` on success; `404` if `voice` isn't in
  the current voice list (`VoiceNotFoundError`).
- `POST /settings/speed` — body `{"speed": 1.0}`. `200`, always succeeds (silently clamped).

## Acceptance criteria

1. `application/ports/tts_port.py`: add abstract `supports_voice_upload()` / `add_voice()`;
   `domain/exceptions.py`: add `VoiceUploadNotSupportedError`.
2. All four adapters (`coqui_tts_adapter.py`, `espeak_ng_adapter.py`, `marytts_adapter.py`,
   `magpie_tts_adapter.py`) implement both new methods.
3. `CoquiTTSAdapter.add_voice` is path-traversal-safe (basename only) and rejects non-`.wav`
   filenames.
4. `application/use_cases/manage_voices_use_case.py`: `ManageVoicesUseCase` with `list_voices`,
   `upload_voice`, `select_voice`, `set_speed`.
5. `adapters/driving/api/routes.py` (or a new `voice_routes.py`): the four endpoints above,
   wired via a `get_manage_voices_use_case` dependency on `app.state`.
6. `api_server.py` wires `ManageVoicesUseCase` (reusing the same `AudioVideoGenerator` instance
   `ProcessQueueUseCase` already uses) into `create_app`.
7. `requirements.txt` gets `python-multipart==0.0.20`.
8. Tests: unit tests for `ManageVoicesUseCase` (fake `TextToSpeechPort` + fake
   `VoiceSettingsManager`), unit tests for `CoquiTTSAdapter.add_voice` (real temp directory, real
   file write, path-traversal + extension rejection cases) and for the other three adapters'
   `supports_voice_upload`/`add_voice` behavior; integration test driving all four endpoints via
   `TestClient` (including a real multipart upload).
9. `WindowTaskQueueManager`/`app.py`'s Tkinter flow unchanged.

## Out of scope

Frontend (#18/#19). Deleting/renaming existing voices (issue only asks for list/upload/select).
Per-adapter `voices_dir` configurability via `pkg/config.py` (not touched by this issue; already
a constructor default today).
