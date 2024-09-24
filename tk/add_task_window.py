import tkinter as tk
from tkinter import scrolledtext, messagebox
from models.task import Task


class AddTaskWindow:
    def __init__(self, root, callback, on_close):
        self.callback = callback
        self.on_close = on_close
        self.floating_window = tk.Toplevel(root)
        self.floating_window.title("Enter your task text")
        self.floating_window.geometry(f"{self.floating_window.winfo_screenwidth()}x400")

        self.create_widgets()

    def create_widgets(self):
        self.floating_window.grid_rowconfigure(0, weight=1)
        self.floating_window.grid_columnconfigure(0, weight=1)

        self.text_box = scrolledtext.ScrolledText(self.floating_window, wrap=tk.WORD)
        self.text_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        button_frame = tk.Frame(self.floating_window)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        accept_button = tk.Button(button_frame, text="Accept", command=self.process_input)
        accept_button.pack(side=tk.RIGHT)

        self.floating_window.grab_set()

        self.floating_window.grid_rowconfigure(1, weight=0)


    def process_input(self):
        input_text = self.text_box.get("1.0", tk.END).strip()
        text_to_speak = Task.validate_input(input_text)
        if text_to_speak:
            self.callback(text_to_speak)
            self.floating_window.destroy()
            self.on_close()
