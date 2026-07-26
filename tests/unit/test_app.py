from unittest.mock import patch

import pytest

from app import build_tts_engine


def test_build_tts_engine_defaults_to_coqui():
    with patch("app.CoquiTTSAdapter") as mock_coqui_cls:
        engine = build_tts_engine("coqui")

    mock_coqui_cls.assert_called_once_with()
    assert engine == mock_coqui_cls.return_value


def test_build_tts_engine_selects_magpie():
    with patch("app.MagpieTTSAdapter") as mock_magpie_cls:
        engine = build_tts_engine("magpie")

    mock_magpie_cls.assert_called_once_with()
    assert engine == mock_magpie_cls.return_value


def test_build_tts_engine_raises_on_unknown_engine():
    with pytest.raises(ValueError):
        build_tts_engine("unknown-engine")
