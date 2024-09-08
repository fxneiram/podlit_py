import os
from pydub import AudioSegment
from moviepy.editor import AudioFileClip, ColorClip, ImageClip, VideoFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from tqdm import tqdm
import config as cfg


# Función de ejemplo para generar el fragmento de video por cada archivo de audio
def generate_fragment(path_to_audio, text, output_file):
    width, height = 1280, 720
    background_color = (60, 60, 60)
    text_color = (255, 255, 255)
    font_size = 50
    max_width = 1200    
    
    # Crear una imagen con el texto
    font = ImageFont.truetype('arial.ttf', font_size)
    image = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(image)

    # Envolver el texto
    lines = wrap_text(text, font, max_width)

    text_height = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines)
    y_offset = (height - text_height) // 2

    # Dibujar el texto
    for line in lines:
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) / 2
        draw.text((text_x, y_offset), line, fill=text_color, font=font)
        y_offset += bbox[3] - bbox[1]

    # Convertir imagen a array de numpy para MoviePy
    image_array = np.array(image)

    # Crear un ImageClip con la imagen y la duración del audio
    audio_clip = AudioFileClip(path_to_audio)
    duration = audio_clip.duration
    image_clip = ImageClip(image_array, duration=duration)

    # Sincronizar el audio con la imagen
    video_clip = image_clip.set_audio(audio_clip)

    # Exportar el fragmento de video
    video_clip.write_videofile(output_file, fps=24)

def wrap_text(text, font, max_width):
    """Envuelve el texto para que se ajuste al ancho máximo especificado."""
    lines = []
    words = text.split()
    line = ""
    for word in words:
        # Prueba agregar la palabra a la línea actual
        test_line = f"{line} {word}".strip()
        # Usa textbbox para obtener las dimensiones del texto
        bbox = font.getbbox(test_line)
        text_width = bbox[2] - bbox[0]
        if text_width <= max_width:
            line = test_line
        else:
            # La línea actual está completa, agregarla a las líneas
            lines.append(line)
            line = word
    # Agregar la última línea
    if line:
        lines.append(line)
    return lines

def combine_video_fragments(fragments, output_path, delay_ms=500):
    """Combina fragmentos de video en un solo video con un delay entre ellos."""
    clips = []
    delay_duration = delay_ms / 1000.0  # Convertir de milisegundos a segundos

    # Definir un clip de color sólido (negro) para el delay
    delay_clip = ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=delay_duration)  # Ajusta el tamaño según tu video

    for fragment in fragments:
        video_clip = VideoFileClip(fragment)
        clips.append(video_clip)
        clips.append(delay_clip)

    # Concatenar todos los clips (fragmentos + delay)
    final_clip = concatenate_videoclips(clips, method="compose")
    
    # Exportar el video combinado
    final_clip.write_videofile(output_path, fps=24)
