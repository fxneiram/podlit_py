import tkinter as tk
from tkinter import scrolledtext, messagebox
import ast

class TaskWindow:
    def __init__(self, root, callback, on_close):
        self.callback = callback
        self.on_close = on_close
        self.ventana_flotante = tk.Toplevel(root)
        self.ventana_flotante.title("Ingrese su texto")
        self.ventana_flotante.geometry(f"{self.ventana_flotante.winfo_screenwidth()}x400")
        
        self.create_widgets()

    def create_widgets(self):
        # Configurar filas y columnas de la ventana flotante
        self.ventana_flotante.grid_rowconfigure(0, weight=1)
        self.ventana_flotante.grid_columnconfigure(0, weight=1)

        # Crear área de texto con scroll y colocarla en la parte superior
        self.texto = scrolledtext.ScrolledText(self.ventana_flotante, wrap=tk.WORD)
        self.texto.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Crear un marco para el botón en la parte inferior
        frame_boton = tk.Frame(self.ventana_flotante)
        frame_boton.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # Botón para validar y aceptar el texto
        boton_aceptar = tk.Button(frame_boton, text="Aceptar", command=self.process_input)
        boton_aceptar.pack(side=tk.RIGHT)

        # Asegurar que la ventana sea modal
        self.ventana_flotante.grab_set()

        # Configurar la fila del botón para que no se expanda más de lo necesario
        self.ventana_flotante.grid_rowconfigure(1, weight=0)



    def validate_input(self, text):
        try:
            parsed_text = ast.literal_eval(text)
            if not isinstance(parsed_text, dict):
                raise ValueError("El formato debe ser un diccionario.")

            for key, value in parsed_text.items():
                if not isinstance(key, int):
                    raise ValueError(f"La clave {key} no es un entero.")
                if "text" not in value or "language" not in value:
                    raise ValueError(f"El formato de la entrada {key} no es correcto.")
                if not isinstance(value["text"], str) or not isinstance(value["language"], str):
                    raise ValueError(f"Las entradas de 'text' o 'language' en {key} no son cadenas.")
            return parsed_text
        except Exception as e:
            messagebox.showerror("Error de Formato", f"El texto ingresado no es válido:\n{e}")
            return None

    def process_input(self):
        texto_ingresado = self.texto.get("1.0", tk.END).strip()
        text_to_speak = self.validate_input(texto_ingresado)
        if text_to_speak:
            self.callback(text_to_speak)
            self.ventana_flotante.destroy()
            self.on_close()
