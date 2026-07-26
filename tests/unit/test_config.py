import importlib

from pkg import config as cfg


def test_tts_engine_defaults_to_coqui_when_env_var_unset(monkeypatch):
    monkeypatch.delenv("TTS_ENGINE", raising=False)
    importlib.reload(cfg)

    assert cfg.TTS_ENGINE == "coqui"


def test_tts_engine_honors_env_var_override(monkeypatch):
    monkeypatch.setenv("TTS_ENGINE", "magpie")
    importlib.reload(cfg)

    assert cfg.TTS_ENGINE == "magpie"
