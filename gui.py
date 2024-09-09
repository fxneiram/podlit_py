import tkinter as tk
from tkinter import scrolledtext, messagebox
import ast

def mostrar_ventana(callback):
    ventana_flotante = tk.Toplevel()
    ventana_flotante.title("Ingrese su texto")

    texto = scrolledtext.ScrolledText(ventana_flotante, wrap=tk.WORD, width=60, height=20)
    texto.pack(padx=10, pady=10)

    def validar_formato(text):
        try:
            parsed_text = ast.literal_eval(text)

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

    def procesar_texto():
        texto_ingresado = texto.get("1.0", tk.END).strip()
        text_to_speak = validar_formato(texto_ingresado)
        if text_to_speak:
            print("Texto válido:", text_to_speak)
            callback(text_to_speak)
            ventana_flotante.destroy()

    boton_aceptar = tk.Button(ventana_flotante, text="Aceptar", command=procesar_texto)
    boton_aceptar.pack(pady=10)

