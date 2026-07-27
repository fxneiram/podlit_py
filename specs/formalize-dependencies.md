# Formalize dependencies: requirements.txt + requirements-dev.txt

Source: https://github.com/fxneiram/podlit_py/issues/39
Branch: feature/formalize-dependencies

## Problem / goal

`Makefile`'s `install-deps` runs five separate, unpinned `pip install` commands. This "works"
today only because of **install order**, and the real conflict underneath it is worse than it
looks: `opencv-python` (as currently resolved, unpinned) requires `numpy>=2`, while
`TTS==0.22.0` itself declares an **exact** `numpy==1.22.0` dependency for `python_version<=3.10`
— not `numpy==1.26.4` as the Makefile's own comment claimed. Confirmed by actually trying to
resolve `numpy==1.26.4` alongside `TTS==0.22.0` in a single `pip install`: pip's resolver
rejects it outright (`ResolutionImpossible` — "tts 0.22.0 depends on numpy==1.22.0"). The
Makefile's sequential installs papered over this by installing whatever numpy version was
specified *last*, silently overriding both `opencv-python`'s and `TTS`'s own declared
requirements — not a real, resolvable dependency set, and not even the version TTS itself asks
for.

## Design

**`requirements.txt` + `requirements-dev.txt`, not `pyproject.toml` dependencies.** `torch`/
`torchaudio` need the CPU wheel index (`--extra-index-url https://download.pytorch.org/whl/cpu`)
— `requirements.txt` supports that directive natively; PEP 621's `[project.dependencies]` in
`pyproject.toml` has no clean per-package index equivalent. `pyproject.toml` keeps its existing
job (tool config for ruff/mypy/pytest); dependency *versions* live in these two files.

**All production dependencies resolved together, in one `pip install -r requirements.txt` call**
— this is what actually fixes the underlying problem, not just documents it. Verified real,
current version pins (checked against what actually installs cleanly on this project's Python
3.9 target — see "Version pins" below) rather than repeating whatever happened to already be
installed on someone's machine:

- **`numpy==1.22.0`**, not `1.26.4`. `TTS==0.22.0` declares this exact version as its own
  dependency for `python_version<=3.10` — this is what actually gets used to build/import its
  C extensions, not whatever the Makefile happened to install last. Verified by installing the
  full `requirements.txt` in a real Python 3.9 venv and running this project's entire test
  suite (50 tests, including the real Coqui/XTTS-v2 integration test) against it — all green,
  no regression from the `1.26.4` → `1.22.0` change.
- **`opencv-python==4.11.0.86`** (not the latest, `5.0.0.93`) — confirmed by checking each
  version's PyPI metadata: `4.12.0.88` and later require `numpy>=2`, incompatible with numpy 1.x
  entirely; `4.11.0.86` is the newest version still compatible with `numpy==1.22.0`.
- **`torch==2.8.0` / `torchaudio==2.8.0`** — the exact versions this project's own CI already
  resolves to on Python 3.9 (confirmed from a real, green CI run's install log), now pinned
  instead of left to "whatever's latest today."
- **`spacy<3.8` / `bangla<0.0.3`** — the two Python-3.9-incompatibility pins already discovered
  the hard way in #35/PR #48 (spacy's newer releases need Python ≥3.10; bangla 0.0.3+ uses
  `bool | None` syntax that TypeErrors on 3.9), now formalized as part of the single dependency
  file instead of living only as CI-specific `pip install` steps.
- **`TTS==0.22.0`**, **`pydub==0.25.1`** — already-known/verified pins.

**Dev tools pinned too** (`requirements-dev.txt`, `-r requirements.txt` plus `ruff`/`mypy`/
`pytest`), to the versions already validated throughout this session's work (`ruff==0.16.0`,
`mypy==1.11.2`, `pytest==7.4.4`) rather than "whatever's latest" — CI and local dev currently
resolve these independently and can drift (CI has been resolving a newer `pytest` than what's
used locally).

**Makefile and CI updated to use these files** — `make install-deps` becomes
`pip install -r requirements.txt`; a new `make install-dev-deps` target uses
`requirements-dev.txt` (for contributors, not part of `make install` since running the app
doesn't need lint/test tools); CI's "Install project dependencies" + "Install dev tools" steps
collapse into one `pip install -r requirements-dev.txt`.

## Local validation

`brew install python@3.9 python-tk@3.9` to get a real Python 3.9 interpreter locally (this
project's Python 3.12 sandbox default can't validate `TTS==0.22.0`, which doesn't support
≥3.12) — then, in a fresh venv: `pip install -r requirements.txt` resolved cleanly in one pass
(no `ResolutionImpossible`), and the full test suite (50 tests, `ruff`, `mypy`) passed against
it. This is real, not just "should work on paper" — the numpy version change alone
(`1.26.4` → `1.22.0`) was worth verifying against the actual Coqui/XTTS-v2 integration test,
not just assumed safe.

## Acceptance criteria

1. `requirements.txt`: production deps with verified, compatible pins (including the
   `spacy`/`bangla` transitive-dependency pins), resolvable in a single `pip install -r` call.
2. `requirements-dev.txt`: `-r requirements.txt` plus pinned `ruff`/`mypy`/`pytest`.
3. `Makefile`'s `install-deps` target uses `pip install -r requirements.txt`; new
   `install-dev-deps` target uses `requirements-dev.txt`.
4. `.github/workflows/ci.yml`'s dependency-install steps use `requirements-dev.txt` (one step
   instead of the previous six separate `pip install` commands).
5. `espeak-ng`/`ffmpeg` (system binaries, not pip packages) and `nemo_toolkit` (deliberately
   excluded, per #35/#37) are unaffected — this issue is about the pip-installable dependency
   set only.
6. CI passes with the new, unified install.

## Out of scope

Docker/`requirements.txt` for a web backend (#40 — no backend exists yet). Splitting
`pkg/config.py` or any other non-dependency-management refactor.
