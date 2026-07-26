# Spike: evaluate local TTS engines with real SSML support

Source: https://github.com/fxneiram/podlit_py/issues/33
Branch: feature/tts-engine-spike

## Problem / goal

Coqui TTS (XTTS v2) — the engine this project uses today — cannot take SSML input at all; that's
a limitation of the model architecture, not a maintenance issue. Épica C (SSML/prosody, issues
#26-#31) is blocked until we pick a replacement engine that can actually consume SSML markup
(`break`, `prosody`, `emphasis`, `say-as`). This spike's only deliverable is that decision, with
justification, so #34 (design the `TTSEngine`/`TextToSpeechPort` interface) can start from a
concrete target instead of a hypothetical one.

## Scope

Evaluate Mimic 3, MaryTTS, and eSpeak-NG (as required by the issue), plus Piper (already used as
the informal quality benchmark in `PodLitPy_v2_plan.md`) and anything materially new since that
plan was written. Produce a recommendation and post it as a comment on issue #33. This spike does
not touch any code — no adapter, no `TTSEngine` interface, nothing under `fh/`/`adapters/`. That
starts in #34/#35.

## Research findings (as of July 2026)

This project runs TTS inference on CPU only — `Makefile`'s `install-deps` installs the CPU wheel
of `torch`/`torchaudio` explicitly (no CUDA), and `AudioVideoGenerator` merely falls back to CPU
if `torch.cuda.is_available()` is false, which it always will be for anyone following the current
install instructions. So CPU performance is a real, not hypothetical, factor here — the baseline
to beat is "however fast XTTS v2 already generates on your CPU today."

| Engine | SSML support | Voice quality | CPU performance | Maintenance | License | Install | Voice-cloning equivalent |
|---|---|---|---|---|---|---|---|
| **Mimic 3** | `--ssml` flag, real subset | Neural, good | Neural vocoder — its own docs recommend CUDA/GPU for speed; noticeably slower than the non-neural options on CPU-only hardware | **Unmaintained** — MycroftAI itself now points users to Piper as the successor project | Apache-2.0 | pip (`mycroft-mimic3-tts[all]`) or Docker | No |
| **MaryTTS** | Comprehensive — `prosody`, `break`/`s`/`p`, `say-as`, `emphasis`, `voice`, `sub` are all part of its native MaryXML pipeline (SSML tags map directly to it) | Media — HMM/unit-selection era, not neural; a real step down from XTTS v2 | HMM/unit-selection synthesis was designed for CPU-only hardware from the start (no neural vocoder at all) — no published RTF found, but algorithmically far lighter than any neural model here | Actively maintained (Multimodal Speech Processing Group, DFKI/Idiap-affiliated academic group) | LGPL v3 (some Apache-licensed components) | Docker (Java server, e.g. `synesthesiam/marytts`) | No |
| **eSpeak-NG** | Broadest real coverage found: `break`, `prosody`, `emphasis`, `say-as`, `voice`, `mark`, `sub`, `p`/`s` — `phoneme` not confirmed supported | Formant/robotic — clearly the least natural of the four | Fastest by far — RTF ≈ 0.05 (20x faster than real-time), runs on a single 100MHz core with <2MB RAM | Actively maintained | GPL-3.0-or-later | Lightweight native binary/lib, no server, runs fine on modest CPUs | No |
| **Piper** | **Not native.** The original SSML feature request (rhasspy/piper#275) was never resolved before that repo was archived (Oct 2025); only basic pause/emphasis workarounds exist in its successor, `OHF-Voice/piper1-gpl` | Neural, very good — best of the four | Purpose-built for CPU/edge inference (ONNX export) — RTF ≈ 0.2-0.5 depending on benchmark, comfortably faster than real-time even on a Raspberry Pi | Actively maintained (moved to `OHF-Voice/piper1-gpl` after the original repo's archival) | GPL (per the `piper1-gpl` name) | pip (`piper-tts`) | No |

CPU performance ranking, fastest first: **eSpeak-NG > Piper > MaryTTS > Mimic 3.** The two
non-neural engines (eSpeak-NG, MaryTTS) were architected in an era before GPU-dependent neural
vocoders existed, so neither one was ever designed to need acceleration — both should comfortably
beat XTTS v2's current CPU generation time. Mimic 3 being neural *and* CPU-bound (per this
project's install setup) stacks a performance disadvantage on top of its maintenance problem.

Two things worth flagging that change the *framing* of this decision but not the requirement itself:

- **Coqui TTS isn't actually abandoned** — `idiap/coqui-ai-TTS` (PyPI package `coqui-tts`, v0.27.5,
  Jan 2026) is an actively maintained community fork working on current Python/PyTorch. This
  doesn't change the recommendation: XTTS v2 still has no SSML input path at the model level, so
  even a maintained fork doesn't solve Épica C's blocker.
- **Newer neural models (Qwen3-TTS, Orpheus, Chatterbox Multilingual v3) skip SSML entirely** in
  favor of natural-language prosody direction ("speak slowly, warm tone") instead of markup tags.
  Interesting, but out of scope: the issue's acceptance criteria and Épica C's data model
  (`Row`/`Task` gaining an `ssml` field, issue #27) are both framed around actual SSML tags, and
  redesigning that framing is a bigger decision than this spike is scoped for.

## Update (during #35): recommendation reversed — eSpeak-NG is now primary

The recommendation below was made on paper, before either engine was actually run. During #35,
live testing against a real `synesthesiam/marytts:5.2` container (Docker) found that MaryTTS
fails on **both** of the reasons it was picked over Piper:

- **No Spanish voice/locale exists for MaryTTS at all** — confirmed via its own `/locales`
  endpoint (only `te, en_US, en_GB, de, fr, it, sv, ru, tr`), and via research showing MaryTTS
  never officially released one. This is disqualifying on its own: this project's core purpose
  is bilingual EN/ES content.
- **Genuine SSML input throws a server-side `DOMException`** on that image — a longstanding
  MaryTTS bug in its SSML→MaryXML pipeline, not a request-shape mistake (confirmed by testing
  both a hand-built `<maryxml>` document and genuine `<speak>...</speak>` SSML — both fail the
  same way; only `TEXT` and `RAWMARYXML` input types work).

eSpeak-NG — installed as a native binary, no Docker/server needed at all — was live-tested as
the replacement and passed both checks immediately: real Spanish (multiple regional voices:
Spain, Mexico, Venezuela) and real SSML (`<speak>`, `<emphasis>`, `<break>`, `<prosody rate>`)
both worked on the first try. See `specs/espeak-ng-adapter.md` for the adapter built from this.

`MaryTTSAdapter` (built in #35 before this was discovered) stays in the codebase, bugs fixed and
limitations now accurately documented — the port design's whole point was supporting more than
one engine, and a second, more limited implementation costs nothing to keep. But **eSpeak-NG,
not MaryTTS, is the recommendation for #37's cutover.**

## Original recommendation (superseded, kept for context): MaryTTS as primary, eSpeak-NG as a documented fallback

**MaryTTS** is the pick for the primary engine. Reasoning:

- It's the only candidate with *both* comprehensive real SSML support *and* active, non-EOL
  maintenance — Mimic 3 has the SSML fit but is explicitly a dead end (its own maintainers say
  so), and Piper has the maintenance but explicitly lacks the SSML this whole epic exists for.
- `PodLitPy_v2_plan.md`'s own research table already left MaryTTS the least disqualified of the
  four, and issue #40 (Docker/infra) was written anticipating a server-based engine like
  "MaryTTS/Mimic3" — this decision is consistent with what the rest of the plan already assumed.
- The voice-quality regression from XTTS v2 (neural) to MaryTTS (HMM/unit-selection) is real and
  should be validated by ear, not just on paper — that's exactly what #37's regression test
  (Coqui vs. new engine, same script) is for. If that listening test says the quality drop is
  unacceptable for a tool whose whole point is repeated listening (see `CLAUDE.md`'s Purpose
  section), that's grounds to revisit this decision before finishing #35, not after.
- This project runs TTS on CPU only (see the CPU performance note above) — MaryTTS being a
  non-neural, CPU-native design means it's likely a generation-speed *improvement* over today's
  CPU-bound XTTS v2, not just a quality trade-off. That's a real secondary benefit, not just a
  mitigating factor, and worth confirming as part of #37's regression test alongside quality.

**eSpeak-NG is the documented fallback**, not the primary: its SSML coverage is arguably even
broader than MaryTTS's, it's lighter to run (no Java server), and it's actively maintained — but
its robotic voice quality is a bigger regression than MaryTTS's, which matters more here than in a
typical assistant/notification-TTS use case because this project's whole purpose is language
learners *listening repeatedly* to the output. Worth keeping in the `TTSEngine` abstraction
(#34) as a second adapter regardless, since it's cheap to support and useful if MaryTTS's Java
server footprint turns out to be a problem in the Docker setup (#40).

**Ruled out for the primary role**: Mimic 3 (unmaintained upstream, explicitly superseded),
Piper (no real SSML — defeats the point of Épica C).

## Open questions / edge cases

- Spanish voice coverage and quality specifically for MaryTTS wasn't exhaustively verified in this
  spike (voices are added per-language as separate modules) — #35 (adapter implementation) should
  confirm a usable `es` voice exists before committing further.
- None of the four candidates support anything equivalent to XTTS v2's voice-cloning
  (`sample_voices/*.wav`) — this confirms issue #36 (redefine voice management) needs to treat
  "voice" as a catalog selection, not a cloning reference, regardless of which engine is chosen.

## Out of scope

- Newer natural-language-prosody models (Qwen3-TTS, Orpheus, Chatterbox v3) — noted above as a
  future alternative paradigm, not evaluated further here.
- Any code changes (`TTSEngine` interface, adapter implementation, voice management, dependency/
  Makefile updates) — those are #34, #35, #36, #37 respectively.
