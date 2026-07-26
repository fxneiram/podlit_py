import tkinter as tk

from adapters.driven.tts.coqui_tts_adapter import CoquiTTSAdapter
from audio_video_generator import AudioVideoGenerator
from tk.window_task_queue_manager import WindowTaskQueueManager


class App:
    def __init__(self, root):
        self.root = root

        tts_engine = CoquiTTSAdapter()
        media_generator = AudioVideoGenerator(tts_engine=tts_engine)
        self.task_queue_app = WindowTaskQueueManager(self.root, media_generator)

    def run(self):
        self.task_queue_app.run()


if __name__ == "__main__":
    root = tk.Tk()

    app = App(root)
    app.run()
