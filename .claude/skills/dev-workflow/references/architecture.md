# podlit_py environment & architecture reference

Read this when you reach the implementation phase (step 5) of the dev-workflow, or whenever
you need to know where a change belongs or how to get the project running locally.

## Environment setup

The `Makefile` is the source of truth for setup — don't hand-roll `pip install` commands,
since exact versions matter here (this stack has a history of version-sensitive breakage
between torch, TTS, and numpy).

```bash
make install        # runs install-ffmpeg + create-env + install-deps
```

Individual targets, useful when only part of the setup is broken:

- `make install-ffmpeg` — installs Homebrew (if missing) and `ffmpeg` via brew. macOS only.
- `make create-env` — creates a conda env named `tts` on Python 3.9. TTS/torch on this
  project pin to older, CPU-friendly versions, so this env should not be reused for
  unrelated Python work.
- `make install-deps` — resolves `requirements.txt` in a single `pip install -r` call:
  `torch`/`torchaudio` (CPU wheels), `TTS==0.22.0`, `opencv-python==4.11.0.86`, `pydub`,
  `numpy==1.22.0`. The numpy pin matters and is exact for a reason: `TTS==0.22.0` itself
  declares `numpy==1.22.0` as a hard dependency (confirmed by trying to resolve any other numpy
  version alongside it — pip's resolver rejects it outright), and `opencv-python>=4.12.0.88`
  requires `numpy>=2`, which is why that package is pinned below its own latest release too.
  See `requirements.txt`'s comments for the full reasoning.

Always `conda activate tts` before running anything below — the app imports `TTS.api` and
`torch` directly, so it will fail outside this env.

```bash
make run             # python app.py
make clean            # remove __pycache__ and .pyc files
```

## Running and debugging

`make run` launches a Tkinter window (`App` in `app.py`) backed by a task queue manager.
There's no CLI/headless mode — this is a GUI app, so if you're debugging pipeline logic
without wanting to click through the UI, prefer writing a small throwaway script that
imports `AudioVideoGenerator` directly rather than driving the whole window.

First run will download the XTTS v2 model weights (`tts_models/multilingual/multi-dataset/xtts_v2`)
via the `TTS` library — expect a slow first launch and make sure there's disk space and network
access before assuming something is broken.

Generated intermediate files land in `cfg.TEMP_DIR` / `cfg.OUTPUT_DIR` (`./tmp`, `./output`,
gitignored) — check there first when debugging why a video looks wrong, before re-running the
whole pipeline.

## Architecture map (current/legacy layout)

This is the layout as it exists today. The project is migrating this toward a hexagonal
architecture — see [hexagonal-architecture.md](hexagonal-architecture.md) for the target
package layout, and use it (not this flat map) when deciding where new code belongs.

```
app.py                        Entry point: builds AudioVideoGenerator + WindowTaskQueueManager
audio_video_generator.py      AudioVideoGenerator: orchestrates TTS -> audio -> video per task
pkg/config.py                 All paths/colors/sizes/FPS constants — check here before hardcoding
fh/                            Low-level media helpers, one manager per concern:
  haudio.py                    AudioManager — silence padding, audio-level ops
  hvideo.py                    VideoManager — renders a video fragment from text + audio
  hfiles.py                    FileManager — temp/output paths, work folder creation
models/
  task.py                      Task — a named, ordered sequence of Rows; (de)serializes to/from JSON
  row.py                        Row — one (text, lang) pair, the atomic unit of narration
tk/
  window_task_queue_manager.py  Main window: owns the queue, wires UI actions to AudioVideoGenerator
  treeview_task_queue.py        Treeview widget listing queued tasks
```

Data flow for one generation: a `Task` holds ordered `Row`s (text + language). `generate_files`
in `audio_video_generator.py` iterates the rows, calls `TTS.tts_to_file` per row (respecting
`speech_speed`), pads silence via `AudioManager`, renders each row as a video fragment via
`VideoManager`, then hands off to `FileManager`/`fh` to concatenate into the final output. When
changing this flow, keep the per-row loop language-aware — rows can alternate EN/ES within a
single task (see the project's prompt template in `README.md`).

## Working on the Tkinter UI

`tk/window_task_queue_manager.py` owns queue state and wires buttons/menus to
`AudioVideoGenerator` calls; `tk/treeview_task_queue.py` is purely the list widget. Task
persistence (load/save queue to file, edit task name, edit rows) is JSON-based via
`Task.build_from_string` / `Task.validate_input` in `models/task.py` — when adding a new field
to a task, update the JSON schema there first, then the UI, not the other way around.

## Testing notes specific to this repo

`pyproject.toml` already configures `[tool.pytest.ini_options]` (`testpaths = ["tests"]`), ruff,
and mypy — see [coding-standards.md](coding-standards.md). There is no `tests/` directory yet,
though: the first dev-workflow run that adds tests should add `tests/__init__.py`,
`tests/unit/__init__.py`, `tests/integration/__init__.py` alongside it.

Mock these in unit tests — they are slow, heavy, or require a GPU/model download:
- `TTS.api.TTS` (and any `.tts_to_file` calls) in `audio_video_generator.py`
- `torch.cuda.is_available()` — test both branches without needing an actual GPU
- Real ffmpeg/moviepy video rendering in `fh/hvideo.py`

Integration tests may stub only the TTS model call itself (e.g., patch `TTS.tts_to_file` to
write a tiny silent WAV) while letting `AudioManager`, `VideoManager`, and `FileManager` run
for real — that's what actually validates the wiring between them.

## Common pitfalls

- Editing dependency versions without checking why they're pinned (see numpy/TTS note above)
  is the most common way to break this project silently.
- Assuming CPU/GPU: `audio_video_generator.py` auto-selects `cuda` if available, else `cpu` —
  don't assume a codepath is dead just because your machine has no GPU.
- Adding a new constant: put it in `pkg/config.py`, not inline in `fh/` or `tk/` — that file is
  the single place non-code-owners are expected to look for tunables (colors, sizes, FPS, paths).
