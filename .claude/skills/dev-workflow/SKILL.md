---
name: dev-workflow
description: End-to-end development workflow for podlit_py — takes a GitHub issue or a plain instruction and drives it through branch creation, spec-first (SDD) design, TDD (unit tests before code), implementation, integration tests, self-review, PR creation, and CI verification. Use this whenever the user gives you a GitHub issue number/URL to work, or asks to implement a feature, fix a bug, "start work on X", or "open a PR for X" — not just when they explicitly say "follow the dev workflow."
---

# podlit_py development workflow

A disciplined pipeline from "here's an issue" to "here's a green PR". The point of doing
spec → tests → code → integration → review in that exact order is that each phase catches a
different class of mistake early, before it's expensive: the spec catches wrong scope, unit
tests catch wrong behavior, integration tests catch wrong wiring, self-review catches everything
that slips past automated checks. Skipping ahead (e.g. writing code before the spec is agreed,
or opening a PR before checks are green) throws away exactly the safety net that phase provides.

For anything about *how this codebase is built* (Makefile, conda env, module layout,
what to mock in tests) — see [references/architecture.md](references/architecture.md). This
file is about the *process*, not the codebase internals.

This project targets a **hexagonal architecture** (ports & adapters) — domain and application
logic must not depend directly on `TTS`, `torch`, `cv2`, or `tkinter`; those live behind ports
implemented by adapters. See [references/hexagonal-architecture.md](references/hexagonal-architecture.md)
for the target package layout and the incremental migration strategy — step 5 (implementation)
applies it.

All code, comments, commit messages, specs, and PR text are **100% English**, comments are
**added only when necessary** (never to restate what the code already says), and Python code
follows PEP 8 + type hints on anything touched. See
[references/coding-standards.md](references/coding-standards.md) — steps 4, 5, and 7 apply it.

## The phases, in order

1. Intake
2. Create branch
3. Spec first (SDD) — **stop for user confirmation**
4. Unit tests first (TDD, red)
5. Implementation (green)
6. Integration tests
7. Self-review
8. Fix findings
9. Generate PR — **requires explicit user confirmation**
10. Verify CI checks

Don't reorder or silently skip a phase. If the user explicitly asks to skip one for a given
task ("skip the spec, just fix the typo"), that's their call to make per-task — but the default
is the full pipeline.

## 1. Intake

- Given a GitHub issue number or URL: `gh issue view <num> --json number,title,body,labels,url`.
  Treat the issue's title/body/labels as the primary source of scope.
- Given a plain instruction instead: treat the user's message itself as the spec seed — there's
  nothing to fetch.
- If scope is ambiguous or missing something a test would need (acceptance criteria, exact
  expected behavior on edge cases, affected files), ask now. It's much cheaper to ask before a
  branch or any file exists than to redo a spec later.

## 2. Create branch

- Check `git status` first — if there's uncommitted work, stash or ask before switching.
- Base off `develop` (this repo's main branch).
- Name: `feature/<slug>` for new capability, `fix/<slug>` for bug fixes — infer which from
  issue labels (`bug` → fix) or from the instruction's intent. `<slug>` is short kebab-case
  from the issue title/instruction, consistent with existing branches like `feature/edit_task`,
  `fix/add_task_name`.

```bash
git checkout -b feature/<slug>
```

## 3. Spec first (SDD)

Write `specs/<same-slug-as-branch>.md` using [references/spec-template.md](references/spec-template.md).
The spec exists to pin down scope and acceptance criteria *before* a single test or line of code
exists — it's the contract that both the unit tests (step 4) and the self-review (step 7) get
checked against later, so vague criteria here just become vague tests later.

Ask the user any clarifying questions the issue/instruction leaves open — edge cases, exact
expected text/format, error handling behavior, which files are in scope. Resolve these as spec
content, not as assumptions buried in code.

**Stop here.** Show the user the spec and wait for explicit confirmation that it's correct
before writing any test. This is the one phase-gate the user asked to always pause at — treat
"looks fine, keep going" as sufficient, but don't infer approval from silence or move on
speculatively while waiting.

## 4. Unit tests first (TDD — red)

- Location: `tests/unit/`, pytest naming (`test_*.py`), one test module per source module.
- Derive test cases directly from the spec's numbered acceptance criteria — every criterion
  should map to at least one test. If a criterion can't be turned into a test, that's a sign
  the spec needs to be more concrete, not that the criterion should be skipped.
- Run them and confirm they fail for the *right* reason (missing implementation — `ImportError`,
  `NotImplementedError`, wrong return value) rather than a typo in the test itself:

```bash
pytest tests/unit -x
```

- If pytest isn't set up yet, add it (`pip install pytest` inside the `tts` conda env, plus
  `tests/__init__.py` and a minimal pytest config) rather than inventing a different test runner
  — see [references/architecture.md](references/architecture.md) for what to mock (TTS, torch,
  real ffmpeg calls) so unit tests stay fast.
- Tests are code too: English names/assertions, comments only where the *why* of a test case
  isn't obvious from its name — see [references/coding-standards.md](references/coding-standards.md).

## 5. Implementation (green)

- Before writing code, plan the implementation as a sequence of small commits — think in
  terms of the smallest set of reviewable steps that gets from red to green, not "write
  everything, then commit once at the end". A reviewer (human or the self-review in step 7)
  can actually follow a series of small, well-described commits; a single giant diff hides
  where a bug was introduced and makes step 8's fixes harder to isolate.
- Place new code according to the hexagonal layout in
  [references/hexagonal-architecture.md](references/hexagonal-architecture.md): domain logic in
  `domain/`, orchestration in `application/use_cases/` against `application/ports/`, and any
  concrete library/framework code (TTS, video, audio, persistence, Tkinter) in `adapters/`. If
  the change touches a module still living in the old flat layout (`fh/`, `models/`, `tk/`,
  `audio_video_generator.py`), migrate that specific piece as its own early commit — see the
  migration strategy in that reference file. Don't let an unrelated feature/fix balloon into a
  full architecture rewrite in one PR.
- Write the minimum code to make the unit tests pass. Never let `domain/` or `application/`
  import a concrete library directly (`TTS`, `torch`, `cv2`, `tkinter`) — if a use case needs
  new external behavior, add or extend a port first, then implement it in an adapter.
- Follow [references/coding-standards.md](references/coding-standards.md): English identifiers/
  comments, comments only when the code can't express something on its own (a constraint, a
  workaround, a non-obvious invariant), PEP 8 naming, and type hints on anything you write or
  touch.
- Commit as you go, one logical change per commit (e.g. "add Row validation", "extract
  AudioProcessorPort + PydubAudioAdapter", "add speech_speed clamping") — not one commit per
  file and not one commit for the whole feature. Keep any hexagonal-migration commit separate
  from the feature/fix commits that motivated it. Each commit message should describe *why*,
  not just restate the diff. Re-run `pytest tests/unit` before each commit so history doesn't
  contain broken intermediate states.
- Refactor only once everything is green, as its own separate commit(s) — don't mix
  behavior changes and refactoring in the same commit.

## 6. Integration tests

- Location: `tests/integration/`. These exercise real module boundaries together (e.g. Task
  persistence round-trip, or the AudioVideoGenerator wired to the real fh/ managers), stubbing
  only the genuinely expensive/external parts (TTS model inference, GPU calls) rather than
  mocking everything like the unit tests do.
- Every acceptance criterion in the spec that describes an end-to-end/user-visible flow should
  have an integration test driving it, not just isolated unit coverage.

## 7. Self-review

Run `ruff format --check` and `ruff check` first (see
[references/coding-standards.md](references/coding-standards.md)) so formatting/lint noise never
shows up as a review finding. Then invoke the `/code-review` skill against everything changed on
this branch relative to `develop`. Treat its findings as required input to the next phase, not
optional commentary — this is the last automated check before the work becomes visible to
anyone else.

## 8. Fix findings

Apply fixes for confirmed findings, re-running unit + integration tests after each fix. If a
finding reveals the spec itself was wrong or incomplete (not just the code), update
`specs/<slug>.md` to match reality — the spec should remain a truthful record of what was built,
not a stale draft of what was originally guessed.

## 9. Generate PR

Push the branch and open the PR with `gh pr create`, using the spec as the source for the PR
description (link `specs/<slug>.md`, restate its acceptance criteria as a test-plan checklist).

Pushing to the shared remote and opening a PR are both visible, hard-to-fully-reverse actions —
show the user the exact push target and the full PR title/body, and get their explicit
confirmation before running `git push` or `gh pr create`, regardless of how autonomous the rest
of this workflow has been.

## 10. Verify CI checks

```bash
gh pr checks <pr-number> --watch
```

If `--watch` isn't available, poll `gh pr checks <pr-number>` instead. On failure, pull logs
(`gh run view --log-failed`), fix, push, and re-verify. Don't report the workflow as done while
any check is red or still pending.

`.github/workflows/ci.yml` runs `ruff`, `mypy`, and `pytest`. The `ruff`/`mypy` steps are
currently advisory (`continue-on-error: true`) because the legacy codebase predates
[references/coding-standards.md](references/coding-standards.md) — a red `ruff`/`mypy` step is
worth a glance but doesn't block the merge yet. `pytest` is blocking (tolerating only "no tests
collected" until `tests/` has content) — a failing test always blocks.

## Definition of done

Before calling this workflow finished, all of the following should be true:

1. `specs/<slug>.md` reflects what was actually built (updated in step 8 if reality diverged).
2. `pytest tests/unit tests/integration` passes locally.
3. `ruff check .` / `ruff format --check .` / `mypy .` were run and any findings in files you
   touched were addressed (pre-existing findings in untouched files are not your responsibility).
4. `/code-review` findings from step 7 are each fixed or explicitly acknowledged as out of scope.
5. The PR is open, its description links the spec, and every CI check is green (or the only
   red checks are the advisory `ruff`/`mypy` steps noted above).
