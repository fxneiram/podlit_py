import json
import re
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog, scrolledtext


class TreeviewTaskQueue(ttk.Treeview):
    def __init__(self, parent, task_queue, *args, **kwargs):
        self.container = tk.Frame(parent)
        self.container.grid(row=0, column=0, sticky="nsew")

        # Crear el widget ScrolledText (cuadro de texto con scroll) en la columna 1 (Derecha)
        self.text_box = scrolledtext.ScrolledText(self.container, wrap=tk.WORD)
        self.text_box.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Configurar colores para el text_box (similar a un IDE)
        self.text_box.configure(bg="#282c34", fg="#abb2bf", insertbackground="white")  # Fondo oscuro, texto claro
        self.text_box.tag_configure("brace", foreground="#61afef")  # Color para {}
        self.text_box.tag_configure("quote", foreground="#98c379")  # Color para ""
        self.text_box.tag_configure("colon", foreground="#e06c75")  # Color para :
        self.text_box.tag_configure("key", foreground="#d19a66")    # Color para claves JSON

        self.save_button = tk.Button(self.container, text="Update Task", command=self.save_task)
        self.save_button.grid(row=1, column=1, sticky="ew", padx=10, pady=10)

        # Configurar el Treeview
        super().__init__(self.container, columns=("Task", "Progress", "Status"), show="headings", *args, **kwargs)
        self.heading("Task", text="Task Queue")
        self.heading("Progress", text="Progress")
        self.heading("Status", text="Status")
        self.column("Progress", width=40)
        self.column("Status", width=100)

        # Colocar el Treeview en la columna 0 del contenedor (Izquierda)
        self.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        # Configurar el layout del contenedor para que se expandan los widgets
        self.container.grid_columnconfigure(0, weight=1)  # Para el Treeview
        self.container.grid_columnconfigure(1, weight=1)  # Para ScrolledText y botón Guardar
        self.container.grid_rowconfigure(0, weight=1)  # Primera fila para ScrolledText y Treeview
        self.container.grid_rowconfigure(1, weight=0)  # Segunda fila para el botón Guardar

        # Enlace a la lista de tareas
        self.task_queue = task_queue

        # Menú contextual
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Edit Name", command=self.edit_selected_task_name)
        self.menu.add_command(label="Delete", command=self.delete_selected_task)
        self.bind("<Button-3>", self.show_context_menu)

        # Evento para seleccionar una fila y cargar el nombre en el cuadro de texto
        self.bind("<<TreeviewSelect>>", self.load_selected_task)

    def save_task(self):
        selected_items = self.selection()
        if not selected_items:
            return

        item = selected_items[0]
        index = self.index(item)

        task_data = self.text_box.get("1.0", tk.END).strip()

        try:
            task_data = json.loads(task_data)
            self.task_queue[index] = task_data
            messagebox.showinfo("Info", "Task updated successfully.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON data.")

    def insert_colored_json(self, json_text):
        brace_pattern = r"[{}]"
        quote_pattern = r'"[^"]*"'
        colon_pattern = r":"
        key_pattern = r'"(\w+)":'

        self.text_box.insert("1.0", json_text)

        for match in re.finditer(brace_pattern, json_text):
            start, end = match.span()
            self.text_box.tag_add("brace", f"1.0+{start}c", f"1.0+{end}c")

        for match in re.finditer(quote_pattern, json_text):
            start, end = match.span()
            self.text_box.tag_add("quote", f"1.0+{start}c", f"1.0+{end}c")

        for match in re.finditer(colon_pattern, json_text):
            start, end = match.span()
            self.text_box.tag_add("colon", f"1.0+{start}c", f"1.0+{end}c")

        for match in re.finditer(key_pattern, json_text):
            start, end = match.span(1)
            self.text_box.tag_add("key", f"1.0+{start}c", f"1.0+{end}c")

    def load_selected_task(self, event):
        selected_items = self.selection()
        if not selected_items:
            return

        item = selected_items[0]
        index = self.index(item)

        self.text_box.delete("1.0", tk.END)

        task_data = self.task_queue[index]
        formatted_json = json.dumps(task_data, indent=4, ensure_ascii=False)

        self.insert_colored_json(formatted_json)

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
