# tabbed_window.py
import tkinter as tk
from tkinter import ttk

class TabbedWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Tabbed Window")
        self.geometry("400x300")

        # Crear el notebook (contenedor de pestañas)
        notebook = ttk.Notebook(self)

        # Crear los frames (paneles) para cada pestaña
        tab1 = ttk.Frame(notebook)
        tab2 = ttk.Frame(notebook)

        # Añadir las pestañas al notebook
        notebook.add(tab1, text="Tab 1")
        notebook.add(tab2, text="Tab 2")

        # Posicionar el notebook en la ventana
        notebook.pack(expand=True, fill="both")

        # Añadir contenido a las pestañas
        label1 = ttk.Label(tab1, text="This is Tab 1")
        label1.pack(pady=20)

        label2 = ttk.Label(tab2, text="This is Tab 2")
        label2.pack(pady=20)

