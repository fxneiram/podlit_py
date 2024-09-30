import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog


class TreeviewTaskQueue(ttk.Treeview):
    def __init__(self, parent, task_queue, *args, **kwargs):
        super().__init__(parent, columns=("Task", "Progress", "Status"), show="headings", *args, **kwargs)
        self.heading("Task", text="Task Queue")
        self.heading("Progress", text="Progress")
        self.heading("Status", text="Status")
        self.column("Progress", width=40)
        self.column("Status", width=100)
        self.grid(row=0, column=0, sticky="nsew")

        # Menú contextual
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Edit Name", command=self.edit_selected_task_name)
        self.menu.add_command(label="Delete", command=self.delete_selected_task)
        self.bind("<Button-3>", self.show_context_menu)

        self.task_queue = task_queue

    def add_task(self, task):
        if 1 in task and "text" in task[1]:
            display_text = task[1]["text"]
        else:
            display_text = "Unknown Task"

        self.task_queue.append(task)
        self.insert("", "end", values=(display_text, "0%", "Pending"))

    def delete_selected_task(self):
        selected_items = self.selection()
        if not selected_items:
            messagebox.showinfo("Info", "No task selected.")
            return

        for item in selected_items:
            task_text = self.item(item, 'values')[0]
            self.delete(item)

            task_to_delete = None
            for task in self.task_queue:
                if task[1]["text"] == task_text:
                    task_to_delete = task
                    break

            if task_to_delete:
                self.task_queue.remove(task_to_delete)

    def edit_selected_task_name(self):
        selected_items = self.selection()
        if not selected_items:
            messagebox.showinfo("Info", "No task selected.")
            return

        item = selected_items[0]
        current_task_name = self.item(item, 'values')[0]

        new_task_name = simpledialog.askstring("Edit Task", "Enter new task name:", initialvalue=current_task_name)

        if new_task_name:
            self.set(item, column="Task", value=new_task_name)

            for task in self.task_queue:
                if task[1]["text"] == current_task_name:
                    task[1]["text"] = new_task_name
                    break

    def show_context_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def update_progress_and_status(self, progress, status, index):
        task_id = self.get_children()[index]
        self.set(task_id, column="Progress", value=f"{int(progress)}%")
        self.set(task_id, column="Status", value=status)
