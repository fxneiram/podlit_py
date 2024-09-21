import tkinter as tk
from tkinter import ttk


class QueueNamePopup:
    def __init__(self, parent, callback):
        self.top = tk.Toplevel(parent)
        self.top.title("Queue Name")

        self.top.geometry("300x100")
        self.top.grab_set()

        tk.Label(self.top, text="Queue Name:").pack(padx=10, pady=5)

        self.queue_name_var = tk.StringVar()
        self.queue_name_entry = ttk.Entry(self.top, textvariable=self.queue_name_var)
        self.queue_name_entry.pack(padx=10, pady=5)

        self.accept_button = tk.Button(self.top, text="Accept", command=self.on_accept)
        self.accept_button.pack(pady=10)

        self.callback = callback

    def on_accept(self):
        queue_name = self.queue_name_var.get()
        if queue_name:
            self.callback(queue_name)
            self.top.destroy()
