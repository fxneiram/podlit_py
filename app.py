import tkinter as tk

from adapters.driven.tts.coqui_tts_adapter import CoquiTTSAdapter
from adapters.driven.tts.magpie_tts_adapter import MagpieTTSAdapter
from application.ports.tts_port import TextToSpeechPort
from audio_video_generator import AudioVideoGenerator
from pkg import config as cfg
from tk.window_task_queue_manager import WindowTaskQueueManager


def build_tts_engine(engine_name: str) -> TextToSpeechPort:
    if engine_name == "coqui":
        return CoquiTTSAdapter()
    if engine_name == "magpie":
        return MagpieTTSAdapter()
    raise ValueError(f"Unknown TTS_ENGINE {engine_name!r} (expected 'coqui' or 'magpie')")


class App:
    def __init__(self, root):
        self.root = root

        tts_engine = build_tts_engine(cfg.TTS_ENGINE)
        media_generator = AudioVideoGenerator(tts_engine=tts_engine)
        self.task_queue_app = WindowTaskQueueManager(self.root, media_generator)

    def run(self):
        self.task_queue_app.run()


if __name__ == "__main__":
    root = tk.Tk()

    app = App(root)
    app.run()
