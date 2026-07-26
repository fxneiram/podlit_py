# Implement EspeakNGAdapter — the actual chosen engine (supersedes MaryTTS as primary)

Source: https://github.com/fxneiram/podlit_py/issues/35 (continued)
Branch: feature/marytts-adapter

## Why this exists

Live testing of `MaryTTSAdapter` against a real `synesthesiam/marytts:5.2` container (the only
published tag for that image) found two disqualifying problems for this project specifically:

1. **No Spanish voice/locale exists for MaryTTS at all** — confirmed via its own `/locales`
   endpoint, and via research showing MaryTTS never officially shipped one. This project's core
   purpose (per `CLAUDE.md`) is bilingual EN/ES content — a TTS engine that can't do Spanish
   fails the actual requirement, not just a nice-to-have.
2. **Genuine SSML input is broken** on that server (a longstanding MaryTTS bug: its SSML→MaryXML
   parser throws a `DOMException` on well-formed `<speak>` input), so the *other* reason MaryTTS
   was chosen over Piper doesn't hold up in practice either.

Given the project's explicit priority is multi-language support, and eSpeak-NG was already the
documented fallback with (per the original #33 research) arguably broader real SSML coverage,
this was live-tested as a direct replacement primary — and confirmed working out of the box:
real Spanish voices (multiple regional variants: Spain, Mexico, Venezuela), real SSML
(`<speak>`, `<emphasis>`, `<break time="...">`, `<prosody rate="...">`), no server/Docker needed
at all (native CLI binary).

`MaryTTSAdapter` stays in the codebase (bugs fixed, limitations now accurately documented) as a
second, more limited implementation of the same port — the port design's whole point was
supporting more than one engine without rewriting the core, and it costs nothing to leave it.

## Design

`EspeakNGAdapter` shells out to the `espeak-ng` CLI via `subprocess.run` with an argument list
(never a shell string — see `coding-standards.md`'s subprocess-safety rule).

- `voice`: passed directly as `-v <voice>`. eSpeak-NG's own voice identifiers already encode
  language (e.g. `Spanish_(Latin_America)`, `en-us`), so — unlike MaryTTS/Coqui — this adapter
  doesn't need a separate `language`→locale mapping; `language` is accepted (required by the
  port) but not used to derive anything, since the voice already determines it.
- `speed`: eSpeak-NG has a native words-per-minute knob (`-s <wpm>`, default 175). Converted as
  `round(175 * speed)` — no XML-wrapping hack needed, unlike MaryTTS.
- `is_ssml`: passing `-m` enables eSpeak-NG's own SSML/markup parser. Confirmed by live testing
  that `-s` (rate) and `-m` (SSML, which can carry its own `<prosody rate="...">`) compose
  without conflict — so, unlike `MaryTTSAdapter`, **this adapter does not need to silently
  ignore `speed` when `is_ssml=True`**; both apply together as real SSML semantics intend.
- `list_voices()`: parses `espeak-ng --voices`' `VoiceName` column (4th whitespace-separated
  field).
- Errors: `subprocess.CalledProcessError` (engine failed) or `FileNotFoundError` (binary missing)
  both get wrapped as `TTSEngineUnavailableError`, consistent with the other adapters' contract.

## Acceptance criteria

1. `adapters/driven/tts/espeak_ng_adapter.py` defines `EspeakNGAdapter(TextToSpeechPort)` as
   described above.
2. Unit tests mock `subprocess.run` (fast, no real binary needed) covering: correct argument
   list for plain text, `-m` added for SSML, speed→wpm conversion, `VoiceNotFoundError`,
   `TTSEngineUnavailableError` on both failure modes, `/voices` parsing.
3. **Integration test calls the real `espeak-ng` binary** — no subprocess mocking at all, since
   it's a fast, lightweight, already-installed local tool with nothing "expensive" to stub
   (unlike Coqui/MaryTTS). Wires the real adapter into `AudioVideoGenerator` and asserts a real,
   valid WAV file is produced.
4. `.github/workflows/ci.yml` installs `espeak-ng` (`apt-get install -y espeak-ng`) so that
   integration test runs for real in CI too, not just locally.
5. `app.py` still unchanged (still `CoquiTTSAdapter`) — the actual cutover is #37's job.

## Out of scope

Same as `marytts-adapter.md`: #36 (voice management UX), #37 (cutover/regression test/Makefile),
#40 (this adapter needs none of it, which is itself worth noting in #40 when that issue starts).
