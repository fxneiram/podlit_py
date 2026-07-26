# Implement MaryTTSAdapter for the TextToSpeechPort

Source: https://github.com/fxneiram/podlit_py/issues/35
Branch: feature/marytts-adapter

## Problem / goal

#33's spike recommended MaryTTS as the primary engine to replace Coqui XTTS v2, and #34 built
`TextToSpeechPort` plus a `CoquiTTSAdapter` as the port's first implementation. This issue adds
the second implementation — `MaryTTSAdapter` — talking to a local MaryTTS HTTP server, so the
epic has a concrete alternative engine to actually validate against Coqui in #37.

## Scope

**Included:** `adapters/driven/tts/marytts_adapter.py` implementing `TextToSpeechPort` against
MaryTTS's HTTP `/process`, `/voices` endpoints (documented at
`marytts-runtime/src/main/resources/marytts/server/http/documentation.html` in the MaryTTS repo),
using the standard-library `urllib.request` — no new pip dependency, since formalizing the
project's dependency file is issue #39's job, not this one.

**Not included, deliberately:**
- **Not wired into `app.py`.** `app.py` keeps using `CoquiTTSAdapter` after this issue.  Per #37's
  own description ("Solo tras validar, remover completamente la dependencia de Coqui..."), the
  cutover happens only after the Coqui-vs-MaryTTS regression test in #37 — building the adapter
  and switching the live engine are two different, sequenced decisions.
- **Not standing up the MaryTTS Docker container.** That's #40. This issue assumes a MaryTTS
  server is reachable at a configurable URL; it doesn't provision one.
- **Not touching #36** (redefining voice selection as catalog-based) beyond what's needed for
  `list_voices()`/`voice` to work against MaryTTS's actual voice model (which is catalog-based,
  not cloning-based, confirming what #33/#34 already assumed).

## A verification gap you should know about

I don't have Docker (or any way to run a JVM server) in this environment, so I can't start a real
MaryTTS server and confirm this adapter's HTTP calls actually work against one — only that they
match what MaryTTS's own HTTP documentation describes. Unit/integration tests here mock the HTTP
layer, which proves the adapter is internally consistent (right URL, right params, correct
parsing of a *documented-shape* response) but **not** that it's wire-compatible with a real
server. That real-world check is exactly what #37's regression test does (run the same script
through Coqui and MaryTTS, compare), so treat this adapter as unverified-against-a-live-server
until #37, or until you run `docker run -p 59125:59125 synesthesiam/marytts:5.2` yourself and
smoke-test it.

## API design (from MaryTTS's HTTP docs)

```
GET /process?INPUT_TEXT=...&INPUT_TYPE=TEXT|SSML&OUTPUT_TYPE=AUDIO&AUDIO=WAVE_FILE&LOCALE=...&VOICE=...
GET /voices  -> lines of "name locale gender"
```

- `LOCALE` accepts a bare language code (e.g. `en`) per MaryTTS's own docs — no `en`→`en_US`
  mapping table needed; `language` passes straight through as `LOCALE`.
- `list_voices()` calls `/voices` and returns just the `name` column, in
  `list[str]` — same shape as `CoquiTTSAdapter.list_voices()`, so `AudioVideoGenerator`/UI code
  doesn't need to know which engine is active.
- **`supports_ssml()` returns `True`** — this is the actual point of replacing Coqui. When
  `is_ssml=True`, the caller's content is sent verbatim with `INPUT_TYPE=SSML`; this adapter does
  not modify or re-wrap externally-supplied SSML.
- **Speed, when `is_ssml=False`:** MaryTTS has no simple numeric speed knob for plain text; its
  native rate control is the SSML `<prosody rate="+N%">` element. So when `speed != 1.0` and
  `is_ssml=False`, this adapter wraps the plain content in a minimal MaryXML envelope itself
  (`<maryxml>...<prosody rate="...">TEXT</prosody></maryxml>`) and sends it as `INPUT_TYPE=SSML` —
  converting `speed` (our `[0.1, 3.0]` multiplier) to a percentage via `(speed - 1.0) * 100`
  (e.g. `1.2` → `"+20%"`, `0.8` → `"-20%"`). When `speed == 1.0`, send `INPUT_TYPE=TEXT` plain,
  no wrapping, since there's nothing to adjust. **This means `speed` is silently not applied when
  `is_ssml=True`** — the port doesn't have a way to inject a rate adjustment into caller-supplied
  SSML without risking mangling it, so this adapter assumes SSML callers encode their own desired
  rate directly. Flag if this trade-off needs to change once #30 (SSML integration) exists.
- **Unreachable server**: add `TTSEngineUnavailableError`, a new domain exception, raised when
  the HTTP call fails to connect, instead of letting `urllib.error.URLError` leak through the
  port boundary (same philosophy as `SSMLNotSupportedError`/`VoiceNotFoundError` from #34).

## Naming

- New domain exception: `TTSEngineUnavailableError` in `domain/exceptions.py`, raised on
  connection failure to the MaryTTS server.
- `MaryTTSAdapter.__init__(self, base_url: str = "http://localhost:59125")`.

## Acceptance criteria

1. `adapters/driven/tts/marytts_adapter.py` defines `MaryTTSAdapter(TextToSpeechPort)`:
   - `synthesize(...)`: builds the `/process` query as described above (SSML passthrough,
     TEXT-or-wrapped-for-speed otherwise), writes the response bytes to `output_path`.
   - `list_voices()`: parses `/voices` into a `list[str]` of voice names.
   - `supports_ssml()`: returns `True`.
   - Raises `VoiceNotFoundError` if `voice` isn't in `list_voices()` (mirrors #34's
     `CoquiTTSAdapter` contract), and `TTSEngineUnavailableError` on connection failure.
2. `domain/exceptions.py` gains `TTSEngineUnavailableError`.
3. Unit tests mock `urllib.request.urlopen` (or equivalent) to cover: correct query construction
   for plain TEXT, SSML passthrough, speed-wrapped MaryXML, `VoiceNotFoundError`,
   `TTSEngineUnavailableError` on a connection error, and `/voices` response parsing.
4. Integration test wires the real `MaryTTSAdapter` into `AudioVideoGenerator` (same pattern as
   #34's Coqui wiring test), with the HTTP layer stubbed at the `urllib` boundary rather than a
   hand-written fake, to catch drift the way #34's integration test does for Coqui.
5. `app.py` and `WindowTaskQueueManager` are **unchanged** — still wired to `CoquiTTSAdapter`.

## Open questions for you to confirm

1. Are you comfortable proceeding on the documented-but-unverified API shape above, given I can't
   test against a live MaryTTS server here? Or would you rather hold this issue until you (or a
   session with Docker access) can smoke-test a running container first?
2. OK with stdlib `urllib.request` (no new dependency) rather than pulling in `requests`, given
   #39 hasn't formalized the dependency file yet?
3. OK with the speed-silently-ignored-under-SSML trade-off described above, or should
   `synthesize` raise instead of silently ignoring `speed` when `is_ssml=True` and `speed != 1.0`?

## Out of scope

- #36: full redefinition of voice management UX (this issue only makes `list_voices()`/`voice`
  work correctly against MaryTTS's catalog model).
- #37: Makefile/Dockerfile updates, Coqui-vs-MaryTTS regression test, live-server verification,
  and switching `app.py` to use this adapter.
- #40: MaryTTS Docker container/compose setup.
