from audio_video_generator import AudioVideoGenerator
from tk.window_task_queue_manager import WindowTaskQueueManager
import tkinter as tk


class App:
    def __init__(self, root):
        self.root = root

        media_generator = AudioVideoGenerator()
        self.task_queue_app = WindowTaskQueueManager(self.root, media_generator)
    
    def run(self):
        self.task_queue_app.run()
    

if __name__ == "__main__":
    root = tk.Tk()

    app = App(root)
    app.run()
