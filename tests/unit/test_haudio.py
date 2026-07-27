from pydub import AudioSegment

from fh.haudio import AudioManager
from pkg import config as cfg


def _silent_wav(path, duration_ms):
    AudioSegment.silent(duration=duration_ms).export(str(path), format="wav")
    return path


def test_add_silence_pads_before_and_after(tmp_path):
    audio_path = _silent_wav(tmp_path / "test.wav", 1000)
    manager = AudioManager()

    manager.add_silence(str(audio_path), duration=250, fps=24, before=True, after=True)

    result = AudioSegment.from_wav(str(audio_path))
    assert len(result) >= 1000 + 250 + 250


def test_add_silence_only_before_is_shorter_than_both(tmp_path):
    only_before_path = _silent_wav(tmp_path / "before.wav", 1000)
    both_path = _silent_wav(tmp_path / "both.wav", 1000)
    manager = AudioManager()

    manager.add_silence(str(only_before_path), duration=250, fps=24, before=True, after=False)
    manager.add_silence(str(both_path), duration=250, fps=24, before=True, after=True)

    only_before_result = AudioSegment.from_wav(str(only_before_path))
    both_result = AudioSegment.from_wav(str(both_path))
    assert len(only_before_result) >= 1000 + 250
    assert len(only_before_result) < len(both_result)


def test_add_silence_neither_before_nor_after_only_pads_to_frame_boundary(tmp_path):
    audio_path = _silent_wav(tmp_path / "test.wav", 1003)
    manager = AudioManager()

    manager.add_silence(str(audio_path), duration=250, fps=24, before=False, after=False)

    result = AudioSegment.from_wav(str(audio_path))
    # No before/after silence requested - only frame-boundary rounding should have grown it,
    # so it should stay close to the original duration, not grow by the full 250ms twice.
    assert 1003 <= len(result) < 1003 + 100


def test_add_silence_result_is_aligned_to_frame_boundary(tmp_path):
    fps = 24
    frame_duration_ms = 1000 / fps
    audio_path = _silent_wav(tmp_path / "test.wav", 1003)
    manager = AudioManager()

    manager.add_silence(str(audio_path), duration=0, fps=fps, before=False, after=False)

    result = AudioSegment.from_wav(str(audio_path))
    remainder = len(result) % frame_duration_ms
    assert remainder < 1 or (frame_duration_ms - remainder) < 1


def test_combine_audio_fragments_concatenates_all_inputs(tmp_path, monkeypatch):
    """DURATION_BETWEEN_FRAGMENTS is 0 in this project's actual config, which would make this
    assertion pass identically whether the silence-insertion loop ran 0, 1, or N times - so a
    non-zero gap is patched in here specifically to make the inter-fragment silence count
    something this test can actually fail on."""
    monkeypatch.setattr(cfg, "DURATION_BETWEEN_FRAGMENTS", 100)
    frag1 = _silent_wav(tmp_path / "frag1.wav", 500)
    frag2 = _silent_wav(tmp_path / "frag2.wav", 700)
    output_path = tmp_path / "combined.wav"
    manager = AudioManager()

    manager.combine_audio_fragments([str(frag1), str(frag2)], str(output_path))

    result = AudioSegment.from_wav(str(output_path))
    expected_duration = 100 * 3 + 500 + 700  # one leading silence + one trailing per fragment
    assert abs(len(result) - expected_duration) <= 5


def test_combine_audio_fragments_with_single_fragment(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg, "DURATION_BETWEEN_FRAGMENTS", 100)
    frag = _silent_wav(tmp_path / "frag.wav", 400)
    output_path = tmp_path / "combined.wav"
    manager = AudioManager()

    manager.combine_audio_fragments([str(frag)], str(output_path))

    result = AudioSegment.from_wav(str(output_path))
    expected_duration = 100 * 2 + 400
    assert abs(len(result) - expected_duration) <= 5
