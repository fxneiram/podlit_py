import os
import torch
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import ast
from audio_video_generator import AudioVideoGenerator
from task_window import TaskWindow
import threading

class TaskQueueManager:
    def __init__(self, root):
        self.media_generator = None

        self.root = root
        self.root.title("Gestor de Tareas")
        
        # Lista para almacenar las tareas
        self.task_queue = []
        
        # Marco para la lista de voces y la tabla de tareas
        top_frame = tk.Frame(root)
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew") # Si funciona
        top_frame.grid_columnconfigure(1, weight=1) # No funciona, no se ve nada
        
        # Etiqueta para la lista desplegable
        tk.Label(top_frame, text="Voices:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Obtener los archivos .wav de la carpeta sample_voices
        self.voice_options = self.get_wav_files("sample_voices")
        
       # Crear la lista desplegable para mostrar las voces
        self.voice_combobox = ttk.Combobox(top_frame, values=self.voice_options, state="readonly")
        self.voice_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Seleccionar el primer archivo .wav por defecto si hay alguno
        if self.voice_options:
            self.voice_combobox.current(0)

        # Marco para la tabla de tareas y las barras de progreso
        frame = tk.Frame(root)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Crear la tabla para mostrar las tareas
        self.tree = ttk.Treeview(frame, columns=("Task"), show='headings', height=8)
        self.tree.heading("Task", text="Tareas en Cola")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Crear las barras de progreso
        # Crear las barras de progreso
        self.task_progress = ttk.Progressbar(frame, length=400, mode='determinate')
        self.task_progress.grid(row=1, column=0, pady=5, sticky="ew")

        self.queue_progress = ttk.Progressbar(frame, length=400, mode='determinate')
        self.queue_progress.grid(row=2, column=0, pady=5, sticky="ew")
        
        # Crear los botones
        button_frame = tk.Frame(root)
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        self.add_task_button = tk.Button(button_frame, text="Agregar Tarea", command=self.show_task_window)
        self.add_task_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.process_tasks_button = tk.Button(button_frame, text="Procesar Tareas", command=self.process_tasks)
        self.process_tasks_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.clear_tasks_button = tk.Button(button_frame, text="Limpiar Tareas", command=self.clear_tasks)
        self.clear_tasks_button.grid(row=0, column=2, padx=5, pady=5)

        # Configurar el redimensionamiento
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=0)
        frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_rowconfigure(0, weight=0)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

    def get_wav_files(self, folder_path):
        """Obtiene una lista de archivos .wav de la carpeta sample_voices."""
        if not os.path.exists(folder_path):
            return []
        return [f for f in os.listdir(folder_path) if f.endswith(".wav")]

    def show_task_window(self):
        """Muestra la ventana flotante para agregar una tarea."""
        #mostrar_ventana(self.add_task, self.on_task_window_close)
        TaskWindow(self.root, self.add_task, self.on_task_window_close)

    def add_task(self, task):
        """Añade una tarea a la cola después de validarla."""
        self.task_queue.append(task)
        self.tree.insert("", "end", values=(task,))

    def process_tasks(self):
        """Procesa todas las tareas en la cola una a una, en un hilo separado."""
        if not self.task_queue:
            messagebox.showinfo("Información", "No hay tareas en la cola para procesar.")
            return

        self.init_media_generator()

        total_tasks = len(self.task_queue)
        self.task_queue_index = 0  # Índice para seguimiento de la tarea actual

        def process_next_task():
            """Procesa la siguiente tarea en la cola."""
            if self.task_queue_index >= total_tasks:
                # Al finalizar, vacía la cola de tareas
                self.task_queue.clear()
                self.tree.delete(*self.tree.get_children())  # Limpiar tabla
                self.update_queue_progress(100)
                return

            # Obtener la tarea actual
            task = self.task_queue[self.task_queue_index]
            
            # Procesar la tarea en un hilo separado
            task_thread = threading.Thread(target=self.process_task_in_thread, args=(task,))
            task_thread.start()
            
            # Verifica que el hilo haya terminado antes de avanzar
            def check_thread_done():
                if task_thread.is_alive():
                    self.root.after(100, check_thread_done)
                else:
                    # Avanzar al siguiente índice
                    self.task_queue_index += 1

                    # Actualizar el progreso de la cola
                    self.update_queue_progress(((self.task_queue_index) / total_tasks) * 100)

                    # Procesar la siguiente tarea
                    self.root.after(100, process_next_task)

            check_thread_done()

        # Iniciar el procesamiento de tareas
        process_next_task()



    def process_task_in_thread(self, task):
        """Procesa una sola tarea en un hilo separado."""
        self.process_single_task(task)
        # Actualiza el progreso de la tarea
        self.task_progress['value'] = 100
        self.root.update_idletasks()

    def process_single_task(self, task):
        """Procesa una sola tarea (simulado)."""
        self.task_progress['value'] = 0
        self.root.update_idletasks()

        self.media_generator.generate_files(task, self.update_progress)

    def clear_tasks(self):
        """Limpia todas las tareas en la cola."""
        self.task_queue.clear()
        self.tree.delete(*self.tree.get_children())
        self.update_queue_progress(0)

    def update_progress(self, progress):
        """Actualiza la barra de progreso."""
        self.task_progress['value'] = progress
        self.root.update_idletasks()

    def update_queue_progress(self, progress=0):
        """Actualiza la barra de progreso de la cola según la cantidad de tareas."""
        self.queue_progress['value'] = progress
        self.root.update_idletasks()

    def on_task_window_close(self):
        """Evento para manejar el cierre de la ventana flotante."""
        pass

    def init_media_generator(self):
        sample_voice = f"sample_voices/{self.voice_combobox.get()}"
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tts_model_path = "tts_models/multilingual/multi-dataset/xtts_v2"

        self.media_generator = AudioVideoGenerator(sample_voice, tts_model_path, device=device)

    def run(self):
        """Ejecuta la aplicación."""
        self.root.mainloop()
