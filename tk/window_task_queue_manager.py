import os
import torch
import tkinter as tk
from tkinter import messagebox, ttk
import threading
from audio_video_generator import AudioVideoGenerator
from .add_task_window import AddTaskWindow
from .treeview_task_queue import TreeviewTaskQueue
from .set_queue_name_popup import SetQueueNamePopup


class WindowTaskQueueManager:
    def __init__(self, root):
        self.media_generator = None
        self.root = root
        self.root.title("Pod Lit Py")

        window_width = 800
        window_height = 400

        self.root.geometry(f"{window_width}x{window_height}")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        self.queue_name = ""
        self.task_queue = []
        self.task_delay = 3 * 60 * 1000  # 3 minutes
        self.task_queue_index = 0

        self.processed_tasks = []

        top_frame = tk.Frame(root)
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        tk.Label(top_frame, text="Voices:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.voice_options = self.get_wav_files("sample_voices")
        self.voice_combobox = ttk.Combobox(top_frame, values=self.voice_options, state="readonly")
        self.voice_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        if self.voice_options:
            self.voice_combobox.current(0)

        self.mix_queue_var = tk.BooleanVar(value=True)
        self.mix_queue_checkbox = tk.Checkbutton(top_frame, text="Mix Queue", variable=self.mix_queue_var)
        self.mix_queue_checkbox.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Checkbox for Shutdown on complete
        self.shutdown_var = tk.BooleanVar(value=False)
        self.shutdown_checkbox = tk.Checkbutton(top_frame, text="Shutdown on complete", variable=self.shutdown_var)
        self.shutdown_checkbox.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        frame = tk.Frame(root)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.tree = TreeviewTaskQueue(frame, self.task_queue, height=8)
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

        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

    def get_wav_files(self, folder_path):
        if not os.path.exists(folder_path):
            return []
        return [f for f in os.listdir(folder_path) if f.endswith(".wav")]

    def show_task_window(self):
        AddTaskWindow(self.root, self.tree.add_task, self.on_task_window_close)

    def process_tasks(self):
        if len(self.task_queue) > 1:
            SetQueueNamePopup(self.root, self.handle_queue_name)

        if not self.task_queue:
            messagebox.showinfo("Info", "No tasks to process.")
            return

        self.task_queue_index = 0
        self.init_media_generator()
        self.process_next_task()

    def handle_queue_name(self, queue_name):
        self.queue_name = queue_name

    def process_next_task(self):
        if self.task_queue_index >= len(self.task_queue):
            print('Mix Queue:', self.mix_queue_var.get())
            if self.mix_queue_var.get():
                self.media_generator.combine_queue(self.processed_tasks, file_name=self.queue_name)

            self.processed_tasks.clear()
            self.task_queue.clear()
            self.tree.delete(*self.tree.get_children())
            self.update_queue_progress(100)
            self.processed_tasks = []
            self.queue_name = ""

            # Shutdown if checkbox is checked
            if self.shutdown_var.get():
                self.shutdown_after_completion()

            return

        task = self.task_queue[self.task_queue_index]

        task_thread = threading.Thread(target=self.process_task_in_thread, args=(task,))
        task_thread.start()

        def check_thread_done():
            if task_thread.is_alive():
                self.root.after(100, check_thread_done)
            else:
                self.task_queue_index += 1
                queue_progress = int((self.task_queue_index / len(self.task_queue)) * 100)
                self.update_queue_progress(queue_progress)
                self.root.after(self.task_delay, self.process_next_task)

        check_thread_done()

    def process_task_in_thread(self, task):
        self.process_single_task(task)
        self.task_progress['value'] = 100
        self.root.update_idletasks()

    def process_single_task(self, task):
        self.task_progress['value'] = 0
        self.root.update_idletasks()
        generated_audio, generated_video = self.media_generator.generate_files(task, self.update_progress)
        self.processed_tasks.append((generated_audio, generated_video))

    def clear_tasks(self):
        self.task_queue.clear()
        self.tree.delete(*self.tree.get_children())
        self.update_queue_progress(0)

    def update_progress(self, progress, status="Processing"):
        self.task_progress['value'] = progress
        self.tree.update_progress_and_status(progress, status, self.task_queue_index)
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

    def shutdown_after_completion(self):
        os.system("shutdown /s /f /t 1")

    def run(self):
        self.root.mainloop()
