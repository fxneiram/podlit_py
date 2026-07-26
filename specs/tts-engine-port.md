# Design the TextToSpeechPort abstraction (TTSEngine)

Source: https://github.com/fxneiram/podlit_py/issues/34
Branch: feature/tts-engine-port

## Problem / goal

`AudioVideoGenerator` imports `TTS.api.TTS` and `torch` directly and calls `tts_to_file` inline —
exactly the coupling `hexagonal-architecture.md` flags as the reason unit tests here have to mock
library internals instead of swapping in a fake. This issue defines the interface any TTS engine
implements (`TextToSpeechPort`, the "TTSEngine" of the issue title), so `AudioVideoGenerator`
depends only on that contract and the concrete engine becomes swappable.

## Scope

**Included, and why:** the issue's acceptance bar is "`AudioVideoGenerator` debe depender solo de
esta interfaz, no del motor concreto" — that's not true until something *is* injected in place of
today's direct `TTS.api` call. So this issue also introduces `CoquiTTSAdapter`, a concrete
implementation of the new port that wraps the **existing** Coqui XTTS v2 code path with no
behavior change (same model, same voices, same output). This is the strangler-pattern migration
step from `hexagonal-architecture.md`: "never leave a port half-implemented." The actual
*replacement* engine (MaryTTS, per #33) is #35's job, not this one — #35 adds a second adapter
(`MaryTTSAdapter`) that plugs into the same port this issue defines.

**Also included:** standing up `tests/unit/` and `tests/integration/` with pytest — this is the
first dev-workflow run to touch testable, non-UI code, so the scaffolding `architecture.md`
already anticipated gets created here rather than as a separate issue.

**Not included:** #35 (MaryTTS adapter), #36 (redefining what a "voice" means for a catalog-based
engine — this issue's `list_voices()`/`voice` parameter are intentionally generic strings so #36
isn't blocked, but doesn't re-litigate the `sample_voices/` scheme itself), #37 (dependency/
Makefile updates), and no change to `WindowTaskQueueManager`'s public behavior.

## Interface design

```python
# application/ports/tts_port.py
class TextToSpeechPort(ABC):
    @abstractmethod
    def synthesize(
        self,
        content: str,
        language: str,
        voice: str,
        speed: float,
        output_path: str,
        is_ssml: bool = False,
    ) -> None:
        """Write synthesized audio for `content` to `output_path`."""

    @abstractmethod
    def list_voices(self) -> list[str]:
        """Return the identifiers of voices this engine can use."""

    @abstractmethod
    def supports_ssml(self) -> bool:
        """Whether this engine can accept `is_ssml=True` input."""
```

Design decisions worth confirming explicitly:

- **Stateless port, no `select_voice()`/`change_voice()` method on the interface.** `voice` and
  `speed` are parameters on every `synthesize()` call rather than mutable adapter state. The
  *caller* (`AudioVideoGenerator` today, a future `GenerateMediaUseCase`) is what remembers "the
  currently selected voice" across a queue of tasks — the port itself stays a pure capability
  contract, which is also what makes it trivial to fake in tests (`coding-standards.md`'s
  `FakeTTSAdapter` example). The issue's "seleccionar voz" requirement is satisfied by voice being
  a parameter, not a separate method.
- **`voice` is a plain string identifier, not a file path.** Today, `change_voice` prefixes
  whatever's passed with `sample_voices/`. That filesystem detail moves *into* `CoquiTTSAdapter`
  (it still resolves a bare name to `sample_voices/<name>.wav` internally) so the port itself
  doesn't assume voice-cloning-by-wav-file — future engines (#36) can interpret "voice" as a
  catalog name instead without changing the port.
- **`is_ssml` is an explicit parameter, not two methods.** `synthesize(..., is_ssml=True)` on an
  adapter whose `supports_ssml()` is `False` raises `SSMLNotSupportedError` (new, in
  `domain/exceptions.py`) rather than silently sending markup as literal text or raising a
  library-specific error. This gives #30 ("branch on SSML availability") a single, consistent
  failure mode to check for across engines.
- **Synchronous, file-out, no return value** — matches today's `tts_to_file` pattern exactly
  (`AudioVideoGenerator` already builds the output path upfront via `FileManager`). Not
  introducing async/streaming here; nothing in this codebase needs it yet and speculative
  concurrency support isn't worth the complexity.

## Acceptance criteria

1. `application/ports/tts_port.py` defines `TextToSpeechPort` with `synthesize`, `list_voices`,
   `supports_ssml` as shown above.
2. `domain/exceptions.py` defines `SSMLNotSupportedError` and `VoiceNotFoundError`; adapters raise
   these instead of letting library-specific exceptions leak through the port boundary.
3. `adapters/driven/tts/coqui_tts_adapter.py` implements `TextToSpeechPort` fully:
   `torch`/`TTS.api` imports and the `cuda`/`cpu` device selection live only here; `synthesize`
   raises `SSMLNotSupportedError` when `is_ssml=True`; `list_voices` reads `sample_voices/*.wav`
   exactly as `load_voices()` does today; `supports_ssml()` returns `False`.
4. `AudioVideoGenerator` no longer imports `torch` or `TTS.api`. Its constructor takes a
   `tts_engine: TextToSpeechPort`; `generate_files` calls `tts_engine.synthesize(...)`;
   `load_voices`/`change_voice`/`set_speech_speed` keep their current public signatures (so
   `WindowTaskQueueManager` needs zero changes) but delegate through the port.
5. `app.py` builds one `CoquiTTSAdapter` and injects it into `AudioVideoGenerator` — running
   `make run` produces identical behavior to before this change (same voices listed, same audio
   output for the same input).
6. `tests/unit/test_coqui_tts_adapter.py` and `tests/unit/test_audio_video_generator.py` exist,
   using a `FakeTTSAdapter`/mocked `TTS.api.TTS` respectively, covering: normal synthesis call
   shape, `SSMLNotSupportedError` on `is_ssml=True`, `list_voices()` reading a temp
   `sample_voices/` directory, and speed clamping (existing `[0.1, 3.0]` behavior, unchanged).

## Open questions / edge cases

- None outstanding — the design decisions above cover the ambiguous points from the issue text.
  Flag here if the confirmation step surfaces something else.

## Out of scope

- #35: the MaryTTS adapter (second implementation of this same port).
- #36: redefining voice selection as catalog-based rather than cloning-based — this issue keeps
  `CoquiTTSAdapter`'s existing `sample_voices/*.wav` behavior untouched, just moved behind the port.
- #37: Makefile/dependency updates, Coqui-vs-new-engine regression testing.
- Any change to `WindowTaskQueueManager`, `TreeviewTaskQueue`, or the task queue's dict-based data
  shape.
