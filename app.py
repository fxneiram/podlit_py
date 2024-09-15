from tk.task_queue_manager import TaskQueueManager
import tkinter as tk


class App:
    def __init__(self, root):
        self.root = root
        self.task_queue_app = TaskQueueManager(self.root)
    
    def run(self):
        self.task_queue_app.run()
    

if __name__ == "__main__":
    root = tk.Tk()

    app = App(root)
    app.run()
