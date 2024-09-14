import os
import torch
import tkinter as tk
from tkinter import messagebox, ttk
import threading
from audio_video_generator import AudioVideoGenerator
from task_window import TaskWindow

class TaskQueueManager:
    def __init__(self, root):
        self.media_generator = None
        self.root = root
        self.root.title("Pod Lit Py")

        self.task_queue = []

        top_frame = tk.Frame(root)
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        tk.Label(top_frame, text="Voices:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.voice_options = self.get_wav_files("sample_voices")

        self.voice_combobox = ttk.Combobox(top_frame, values=self.voice_options, state="readonly")
        self.voice_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        if self.voice_options:
            self.voice_combobox.current(0)

        frame = tk.Frame(root)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.tree = ttk.Treeview(frame, columns=("Task"), show='headings', height=8)
        self.tree.heading("Task", text="Task Queue")
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.task_progress = ttk.Progressbar(frame, length=400, mode='determinate')
        self.task_progress.grid(row=1, column=0, pady=5, sticky="ew")

        self.queue_progress = ttk.Progressbar(frame, length=400, mode='determinate')
        self.queue_progress.grid(row=2, column=0, pady=5, sticky="ew")

        button_frame = tk.Frame(root)
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.add_task_button = tk.Button(button_frame, text="Add Task", command=self.show_task_window)
        self.add_task_button.grid(row=0, column=0, padx=5, pady=5)

        self.process_tasks_button = tk.Button(button_frame, text="Process Queue", command=self.process_tasks)
        self.process_tasks_button.grid(row=0, column=1, padx=5, pady=5)

        self.clear_tasks_button = tk.Button(button_frame, text="Clean Queue", command=self.clear_tasks)
        self.clear_tasks_button.grid(row=0, column=2, padx=5, pady=5)

        # Create a menu for the Treeview
        self.tree_menu = tk.Menu(root, tearoff=0)
        self.tree_menu.add_command(label="Delete", command=self.delete_selected_task)

        self.tree.bind("<Button-3>", self.show_context_menu)

        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=0)
        frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_rowconfigure(0, weight=0)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

    def get_wav_files(self, folder_path):
        if not os.path.exists(folder_path):
            return []
        return [f for f in os.listdir(folder_path) if f.endswith(".wav")]

    def show_task_window(self):
        TaskWindow(self.root, self.add_task, self.on_task_window_close)

    def add_task(self, task):
        if 1 in task and "text" in task[1]:
            display_text = task[1]["text"]
        else:
            display_text = "Unknown Task"

        self.task_queue.append(task)
        self.tree.insert("", "end", values=(display_text,))

    def process_tasks(self):
        if not self.task_queue:
            messagebox.showinfo("Info", "No tasks to process.")
            return

        self.init_media_generator()

        total_tasks = len(self.task_queue)
        self.task_queue_index = 0

        def process_next_task():
            if self.task_queue_index >= total_tasks:
                self.task_queue.clear()
                self.tree.delete(*self.tree.get_children())
                self.update_queue_progress(100)
                return

            task = self.task_queue[self.task_queue_index]

            task_thread = threading.Thread(target=self.process_task_in_thread, args=(task,))
            task_thread.start()

            def check_thread_done():
                if task_thread.is_alive():
                    self.root.after(100, check_thread_done)
                else:
                    self.task_queue_index += 1
                    self.update_queue_progress(((self.task_queue_index) / total_tasks) * 100)
                    self.root.after(100, process_next_task)

            check_thread_done()

        process_next_task()

    def process_task_in_thread(self, task):
        self.process_single_task(task)
        self.task_progress['value'] = 100
        self.root.update_idletasks()

    def process_single_task(self, task):
        self.task_progress['value'] = 0
        self.root.update_idletasks()
        self.media_generator.generate_files(task, self.update_progress)

    def clear_tasks(self):
        self.task_queue.clear()
        self.tree.delete(*self.tree.get_children())
        self.update_queue_progress(0)

    def update_progress(self, progress):
        self.task_progress['value'] = progress
        self.root.update_idletasks()

    def update_queue_progress(self, progress=0):
        self.queue_progress['value'] = progress
        self.root.update_idletasks()

    def on_task_window_close(self):
        pass

    def init_media_generator(self):
        sample_voice = f"sample_voices/{self.voice_combobox.get()}"
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tts_model_path = "tts_models/multilingual/multi-dataset/xtts_v2"

        self.media_generator = AudioVideoGenerator(sample_voice, tts_model_path, device=device)

    def delete_selected_task(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "No task selected.")
            return

        for item in selected_items:
            task_text = self.tree.item(item, 'values')[0]
            self.tree.delete(item)

            task_to_delete = None
            for task in self.task_queue:
                if task[1]["text"] == task_text:
                    task_to_delete = task
                    break

            if task_to_delete:
                self.task_queue.remove(task_to_delete)

    def show_context_menu(self, event):
        # Open the context menu at the location of the click
        self.tree_menu.post(event.x_root, event.y_root)

    def run(self):
        self.root.mainloop()
