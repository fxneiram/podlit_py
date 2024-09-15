from tk.task_queue_manager import TaskQueueManager
import tkinter as tk

class App:
    def __init__(self, root, generator):
        self.generator = generator
        self.root = root
        self.task_queue_app = TaskQueueManager(self.root)
    
    def process_task(self, text_to_speak):
        self.generator.generate_files(text_to_speak)
    

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskQueueManager(root)
    app.run()
