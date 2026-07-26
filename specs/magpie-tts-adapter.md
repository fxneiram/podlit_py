# Implement MagpieTTSAdapter — final engine choice (prosody control abandoned)

Source: https://github.com/fxneiram/podlit_py/issues/35 (continued)
Branch: feature/marytts-adapter

## Why this exists

Live testing (this branch) went through three engines for #33/#35:

1. **MaryTTS**: no Spanish, SSML broken on the server — ruled out.
2. **eSpeak-NG**: real Spanish + real SSML, but voice quality is markedly robotic — kept as the
   SSML-capable option, but the user wanted to hear real audio before committing.
3. **MagpieTTS** (`nvidia/magpie_tts_multilingual_357m`, via NeMo): user-suggested. Live-tested
   and confirmed: real Spanish, genuinely neural quality, and — contrary to its own
   documentation, which says GPU is required — **it runs on CPU**, at roughly 4x slower than
   real-time (~16-19s to generate ~4-4.5s of audio). Workable for this project's background
   queue processing, not workable for real-time use.

MagpieTTS's public API (`do_tts`) was exhaustively checked for any prosody control — SSML,
natural-language style description (like Qwen3-TTS/Orpheus offer), even a numeric speed knob —
and has **none**. The only controllable inputs are text, language, and a choice among a handful
of fixed "baked" speaker voices (`model.num_baked_speakers`, confirmed = 5 on this checkpoint).

**Decision, made explicitly by the user with this limitation known**: prioritize voice quality,
accept zero prosody control. This makes Épica C (issues #26-#31, SSML/prosody) moot — its entire
premise was having *some* mechanism to control pacing/emphasis, and the chosen engine has none.
Those issues were closed with an explanatory comment rather than left open as misleading backlog.

`MaryTTSAdapter` and `EspeakNGAdapter` (built earlier in this branch) stay in the codebase as
documented, more-limited implementations of the same port — the port's whole point is supporting
multiple engines without rewriting the core.

## Design

- **Heavy, deferred dependency.** `nemo_toolkit[tts]` must be installed from its `main` git
  branch (the stable PyPI release's tokenizer validation is incompatible with this specific
  checkpoint's config — confirmed by testing: `nemo_toolkit==2.7.3` fails with
  `ValueError: Unsupported locale 'pt-BR'` on load). This is a ~2.2GB install from an unpinned,
  actively-changing branch.
- **Deliberately not added to `Makefile`/CI.** Unlike `torch`/`TTS`/`pydub`/`espeak-ng`, this
  dependency is too heavy and too unstable to install on every CI run or expect in every
  contributor's environment by default. Using `MagpieTTSAdapter` requires a manual, documented
  install (see the adapter's own docstring) — this is an explicit, judgment-call trade-off, not
  an oversight.
- **Tests stub the entire `nemo` package via `sys.modules`**, rather than requiring the real
  (huge, unstable) dependency to be installed to run the test suite. This keeps CI fast and
  deterministic while still testing this adapter's own logic (voice↔speaker-index mapping,
  `is_ssml` rejection, audio writing) against a controlled fake — the same reasoning as
  `CoquiTTSAdapter`'s tests mocking `TTS.api.TTS`, just one level further out since the real
  package isn't even installed in the test environment.
- **Model loaded once in `__init__`** (like `CoquiTTSAdapter`, unlike the stateless
  `MaryTTSAdapter`/`EspeakNGAdapter`) — load takes ~30s, so doing it per `synthesize()` call
  would be prohibitive.
- **`voice`** maps to `speaker_index` (an int 0..`num_baked_speakers - 1`); `list_voices()`
  returns `["speaker_0", ..., f"speaker_{n-1}"]`.
- **`speed`** is accepted (required by the port) but has no effect — there is nothing in
  MagpieTTS's API to apply it to. Not an error; the port contract doesn't require every adapter
  to act on every parameter (see `EspeakNGAdapter`'s unused `language`).
- **`is_ssml=True`** raises `SSMLNotSupportedError` — same as `CoquiTTSAdapter`.
- Output written via `torchaudio.save` (already a project dependency via `torch`/`torchaudio` —
  no need for the extra `soundfile` package used only in this spike's throwaway test script).

## Acceptance criteria

1. `adapters/driven/tts/magpie_tts_adapter.py` defines `MagpieTTSAdapter(TextToSpeechPort)` as
   above.
2. Unit tests stub `nemo.collections.tts.models.MagpieTTSModel` via `sys.modules` — no real
   model load, no real dependency required — covering: speaker-index mapping, `speed` being
   accepted without effect, `SSMLNotSupportedError` on `is_ssml=True`, `VoiceNotFoundError`,
   `list_voices()` derived from `num_baked_speakers`.
3. Integration test wires the (still-stubbed) adapter into `AudioVideoGenerator`, same pattern
   as the Coqui/MaryTTS wiring tests — no real model load here either, for the reasons above.
4. `app.py` **unchanged** — cutover to any engine is #37's job, not this issue's.
5. `Makefile`/CI **unchanged** — `nemo_toolkit` is not added as a standard dependency; the
   adapter's docstring documents the manual install requirement.

## Out of scope

Épica C is closed (see above). #36 (voice management UX), #37 (cutover/regression/Makefile —
now presumably targeting MagpieTTS given this decision), #40 (Docker — not needed for this
engine, since it runs as a Python-in-process model, not a server).
