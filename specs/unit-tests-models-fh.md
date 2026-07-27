# Unit tests for models/task.py, fh/hfiles.py, fh/haudio.py

Source: https://github.com/fxneiram/podlit_py/issues/41
Branch: feature/unit-tests-models-fh

## Problem / goal

`models/task.py`, `models/row.py`, `fh/hfiles.py`, and `fh/haudio.py` have zero test coverage —
all of this session's earlier test work covered the TTS port/adapters and `AudioVideoGenerator`,
not these older, still-untouched modules. This issue closes that gap for the pieces its own
scope names: `models/task.py`, `fh/hfiles.py`, `fh/haudio.py`.

## Scope adjustment

The issue's original scope also asks for "tests de integración para los endpoints de la API
(cola de tareas, generación de contenido con OpenAI mockeado)" — there are no API endpoints yet
(Épica A/B haven't started), so that part is deferred until those epics exist. "Mock del motor
TTS en tests" is already done extensively across this session's earlier work (all four adapters).

## Two real bugs found while adding coverage — fixed as part of this issue, not left for later

Per `coding-standards.md`'s own "fix a module's instances as you touch it" policy, and since
both were already specifically named as anti-patterns in that document:

1. **`Task.validate_input` returns the exception instead of raising it** (`models/task.py:54`).
   Its only caller (`tk/window_task_queue_manager.py`'s `btn_action_add_from_file`) already
   wraps the call in `try/except Exception` — today, a validation failure returns an `Exception`
   object that gets passed straight to `self.tree.add_task(...)` as if it were valid task data,
   which then raises a *second*, unrelated `TypeError` when `add_task` tries to treat the
   exception object like a dict. The user sees a confusing type error instead of the actual
   validation message. Raising directly lets the existing `try/except` catch it correctly and
   show the real error — a strict improvement, not just cleanup.
2. **`AudioManager.combine_audio_fragments` uses `print()`** instead of `logging`
   (`fh/haudio.py:21`) — inconsistent with the `logging` already set up in
   `audio_video_generator.py`. Fixed while adding this file's first tests.

## Testing approach

- `models/task.py`/`models/row.py`: pure logic, no I/O — straightforward unit tests.
- `fh/hfiles.py`: filesystem operations against `tmp_path`, no mocking needed (fast, real disk
  I/O on temp dirs).
- `fh/haudio.py`: generates small **real** silent WAV files via `pydub` (already a project
  dependency) rather than mocking pydub itself — verifies the actual frame-boundary-padding math
  and concatenation behavior for real, similar to this session's "don't mock what's cheap and
  real" approach for `EspeakNGAdapter`'s integration test.

## Acceptance criteria

1. `tests/unit/test_task.py`: `Task.build_from_string` (valid input, invalid JSON, non-dict
   entries, missing text/language keys) and `Task.validate_input` (valid input, non-dict,
   non-integer keys, missing/wrong-typed fields) — the latter now raising, not returning.
2. `tests/unit/test_row.py`: trivial construction/repr coverage.
3. `tests/unit/test_hfiles.py`: `sanitize_filename` (special characters stripped, spaces to
   underscores, edge case of a filename that sanitizes to empty), `get_final_file_names`,
   `generate_random_path` (length, charset), `create_work_folders`/`clean_temp_folders` against
   `tmp_path`.
4. `tests/unit/test_haudio.py`: `add_silence` (padding added before/after, frame-boundary
   rounding), `combine_audio_fragments` (output duration reflects inputs + inter-fragment
   silence), using real small WAV files generated via `pydub.AudioSegment.silent(...)`.
5. `models/task.py` and `fh/haudio.py` source fixes described above land alongside their tests.

## Out of scope

API/integration tests (no API exists yet — deferred to whichever issue actually builds Épica
A's endpoints). `fh/hvideo.py` (heavier — real `cv2`/`PIL`/`ffmpeg` rendering; not named in this
issue's scope, left for a future, separately-scoped pass).
