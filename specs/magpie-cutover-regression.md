# Cutover to MagpieTTS: regression test, Makefile, and removing Coqui

Source: https://github.com/fxneiram/podlit_py/issues/37
Branch: feature/magpie-cutover-regression

## Problem / goal

This is the final step of Épica D: validate MagpieTTS against Coqui XTTS v2 with a real,
side-by-side comparison (not just isolated live tests, which is all that's happened so far),
update the Makefile/dependencies for the new engine, wire `app.py` to actually use it, and only
then consider removing Coqui.

## Scope, resolved with the user

**Makefile**: add a separate, clearly-optional `make install-magpie` target — not part of the
default `make install` chain — so the Makefile documents the install without forcing
`nemo_toolkit`'s ~2.2GB/unpinned `@main`-branch cost on every contributor or CI run.

**No hard cutover.** Rather than switching `app.py` to build `MagpieTTSAdapter` outright, engine
selection becomes **config-driven**: a `TTS_ENGINE` setting (env var, default `"coqui"`) that
`app.py` reads to decide which adapter to build. Coqui stays the default (unchanged behavior for
anyone not opting in); setting `TTS_ENGINE=magpie` switches to `MagpieTTSAdapter` for the
regression comparison and any future full cutover — without deleting or disabling either engine.
This directly enables running the regression test by toggling one config value instead of
editing code, and defers "remove Coqui" indefinitely until it's a deliberate, separate decision.

## Plan

1. **Regression test**: generate the same script (a few EN + ES lines, matching this project's
   real bilingual use case) through both `CoquiTTSAdapter` and `MagpieTTSAdapter` for real (not
   mocked) — reusing the throwaway-venv approach from #35's live testing, since `nemo_toolkit`
   isn't installed in this repo's normal env. Compare: perceived quality (share both audio sets
   with the user, as done in #35), wall-clock generation time, and document known differences
   (voice catalog size/style, language coverage, latency) in this spec.
2. **Config-driven engine selection**: add `TTS_ENGINE` to `pkg/config.py` (env var, default
   `"coqui"`); `app.py` builds `CoquiTTSAdapter()` or `MagpieTTSAdapter()` based on it. The
   `MagpieTTSAdapter`/`nemo_toolkit` import only happens on the `magpie` branch, so the default
   `coqui` path never requires `nemo_toolkit` to be installed.
3. **Makefile**: add `install-magpie` as described above.
4. **No removal of Coqui** in this PR or as a planned next step — both engines stay
   permanently selectable via `TTS_ENGINE`.

## Regression test results

Generated the same 4 lines (2 English, 2 Spanish — matching this project's alternating
bilingual format) through both `CoquiTTSAdapter` and `MagpieTTSAdapter` for real, using a
throwaway venv for MagpieTTS (`nemo_toolkit` isn't installed in this repo's normal env, per the
decision above). Audio shared with the user directly for a by-ear comparison.

**Timing** (CPU, this machine, single voice, no warmup beyond model load):

| Line | Coqui XTTS v2 | MagpieTTS |
|---|---|---|
| EN 1 | 8.2s | ~17s (log-derived) |
| EN 2 | 7.2s | 17.3s |
| ES 1 | 10.5s | 20.9s |
| ES 2 | 8.1s | 19.3s |
| **Total (4 lines)** | **34.0s** | **76.1s** |

MagpieTTS is roughly **2-2.5x slower than Coqui** on this machine's CPU for equivalent short
lines — both are well within "acceptable for background queue processing," but this is a real,
measurable cost of the quality trade-off, not just a theoretical one.

**A third dependency-fragility bug found during this test** (on top of the two already fixed in
#35/PR #48 — the `spacy`/`bangla` Python-3.9 incompatibilities for Coqui's own install, and the
locale/tokenizer version-skew requiring `nemo_toolkit@main`): a **freshly-installed**
`torchaudio` (no version pin) has moved `torchaudio.save`'s default backend to require the
separate `torchcodec` package — without it, `MagpieTTSAdapter.synthesize` fails with
`ImportError: TorchCodec is required for save_with_torchcodec`. Installing `torchcodec`
resolved it. This is exactly the kind of unpinned-version instability the earlier decision to
keep `nemo_toolkit` out of the standard Makefile/CI was meant to avoid — it reinforces that
choice rather than changing it, but `make install-magpie`'s docstring/README guidance should
mention `torchcodec` explicitly so the next person hitting this doesn't have to re-diagnose it.

## Out of scope

#36 (voice management UX redesign — the existing UI already works generically against
`list_voices()`/`change_voice()` regardless of engine, per the port design; #36 is about making
voice selection friendlier, not a blocker here). #40 (Docker — MagpieTTS runs in-process, no
server needed).
