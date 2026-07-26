# Coding standards for podlit_py

Applies to every phase of the dev-workflow that produces code, specs, or commit messages
(steps 3-9). Read this alongside [hexagonal-architecture.md](hexagonal-architecture.md), which
defines architecture-specific naming (`Port`/`Adapter`/`UseCase` suffixes) — this file covers
everything else.

## Language: English, everywhere in the repo

All code artifacts are 100% English: identifiers, docstrings, comments, commit messages,
`specs/*.md` files, and PR titles/descriptions. This applies even though you'll usually be
talking to the user in Spanish — the conversation language and the repo language are
independent, and the repo stays English regardless of what language the request came in.

The current codebase mixes both (e.g. Spanish comments like `# Velocidad del habla` in
`audio_video_generator.py`, `# Menú contextual` in `tk/treeview_task_queue.py`) because this
standard didn't exist yet. Don't do a mass find-and-replace pass to "fix" old comments as a
standalone change — that's churn with no test coverage behind it. Instead, translate a
module's Spanish comments to English as part of any change that already touches that module
(same strangler approach as the hexagonal migration), and write everything new in English from
the start.

## Comments: only when necessary

Default to no comments. Well-named functions, classes, and variables should make the *what*
obvious without narration. Only add a comment when it captures something the code genuinely
can't express on its own:

- a non-obvious constraint (e.g. why `speech_speed` is clamped to `[0.1, 3.0]`)
- a workaround for a specific library/OS quirk (e.g. the font-loading fallback chain in
  `VideoManager.__init__`, or why frame duration is rounded to the FPS boundary before export)
- an invariant that would surprise a future reader (e.g. that the task queue holds plain dicts,
  not `Task`/`Row` instances — see `CLAUDE.md`)

Don't write comments that restate the code (`# loop over rows`), reference the current task or
PR (`# fix for issue #12`), or explain what a well-named function already says. If you're
tempted to add a comment explaining *what* a block does, that's usually a signal to extract it
into a well-named function instead.

## Python style

Follow PEP 8 conventions project-wide:

- `snake_case` for functions, methods, variables, and module names.
- `PascalCase` for classes (domain entities, use cases, ports, adapters alike —
  `AudioProcessorPort`, `PydubAudioAdapter`, `GenerateMediaUseCase`).
- `UPPER_SNAKE_CASE` for module-level constants (as already done in `pkg/config.py` /
  its future home `config/settings.py`).
- Add type hints on function signatures for any code you write or touch — parameters and
  return types. Existing untyped code doesn't need a dedicated typing pass; type it
  incrementally as you touch it, same strangler approach as everything else.
- Write a docstring only where the signature and name don't already make behavior clear
  (e.g. a port's contract, or a use case's non-obvious side effects) — not as boilerplate on
  every function. When you do write one, use **Google-style** docstrings (`Args:`/`Returns:`/
  `Raises:` sections) for consistency — but a one-line docstring beats a multi-paragraph one;
  if you need several paragraphs to explain a function, it's probably doing too much.

## Error handling

Raise typed exceptions from `domain/exceptions.py` (see
[hexagonal-architecture.md](hexagonal-architecture.md)) for domain rule violations, instead of
bare `ValueError`/`Exception`. Two patterns already in this codebase are things to fix when you
touch that code, not things to copy into new code:

- Catching bare `except Exception` and swallowing or just printing it (e.g.
  `audio_video_generator.py`'s temp-folder cleanup retry loop, `window_task_queue_manager.py`'s
  file-read handler) — catch the specific exception you expect and let anything else propagate.
- `Task.validate_input` in `models/task.py` **returns** the exception object instead of raising
  it or returning a clean success/failure result — callers have to check `isinstance(result,
  Exception)`, which is easy to get wrong. When this is touched, replace it with either raising
  a domain exception or an explicit result type, not a function that returns either a value or
  an error depending on what happened.

Adapters are the one place broad exception handling can be legitimate (e.g. retrying a flaky
filesystem operation) — keep it narrow even there, and always log or surface the failure rather
than silently continuing.

## Subprocess safety

Never build a shell command string by interpolating a variable and passing it to `os.system()`
or `subprocess.run(..., shell=True)` — `fh/hvideo.py` does this today for `ffmpeg` calls
(`os.system(f"ffmpeg -i {fragment_tmp} ...")`). It isn't exploitable *yet* because the
interpolated paths are program-generated random names, but it's the exact shape of a command
injection bug, and it's trivial to make safe: use `subprocess.run([...])` with the command and
each argument as separate list items (no shell involved, no quoting to get wrong). Migrate this
when a change touches `fh/hvideo.py` (or its future `adapters/driven/video/` home) rather than
as a standalone drive-by fix.

## Logging, not print

Use the standard `logging` module for status/progress/error output instead of bare `print()`
calls — `audio_video_generator.py` already configures a logger for `moviepy`; extend that same
approach instead of introducing a second, inconsistent way to report status. Reserve `print`
for things a human is meant to read directly off stdout in a CLI/script context, which this
project mostly isn't (it's a GUI app).

## Tooling: ruff (lint + format) and mypy (types)

The repo has no formatter, linter, or type checker configured yet. Use:

- **ruff** for both linting and formatting (no separate `black`/`flake8`/`isort`) —
  `[tool.ruff]` in `pyproject.toml`.
- **mypy** to actually enforce the type hints this document asks for — `[tool.mypy]` in
  `pyproject.toml`. Keep it lenient (`ignore_missing_imports = true`, no blanket
  `disallow_untyped_defs`) while most of the codebase is still untyped; tighten it
  module-by-module as code gets type hints, the same incremental approach as everything else
  here — don't turn on strict mode repo-wide before the code can pass it.

Run `ruff format`, `ruff check`, and `mypy` before the self-review step (7) so mechanical
findings don't show up as review comments — self-review should focus on logic and design.

**Current state**: running `ruff check`/`ruff format --check`/`mypy` against the untouched
legacy code surfaces pre-existing issues (long lines, quote style, missing types) that predate
this standard. `.github/workflows/ci.yml` therefore runs these as advisory (non-blocking) for
now — see the CI note in `SKILL.md` step 10. Don't "fix" unrelated files just to make these
pass; clean up a file's lint/format/type issues when a change already touches it.

## Where this fits in the dev-workflow

- Step 4/5 (tests, implementation): new code follows these conventions from the first line
  written, not as cleanup afterward.
- Step 7 (self-review): run `ruff check`/`ruff format --check`/`mypy` before invoking
  `/code-review`, so the review is about substance.
- Step 9 (PR): PR title/body in English regardless of the language the originating issue or
  instruction was written in.
