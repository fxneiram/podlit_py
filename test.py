import torch
from TTS.api import TTS
from pydub import AudioSegment
from tqdm import tqdm
import os
import config as cfg
import hvideo

SAMPLE_VOICE = "sample_voices/faver_1.wav"
WHITE_NOISE_FILE = "white_noise.mp3"  # Asegúrate de que el archivo sea mp3
SILENCE_DURATION = 500  # 500 ms de silencio

# Obtener el dispositivo
device = "cuda" if torch.cuda.is_available() else "cpu"

# Listar los modelos TTS disponibles
print(TTS().list_models())

# Inicializar TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)

# Directorio para archivos de audio temporales
os.makedirs(cfg.TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(cfg.TEMP_VIDEO_DIR, exist_ok=True)

# Texto a pronunciar
text_to_speak = {
    1: {"text": "Moby-Dick by Herman Melville", "language": "en"},
    2: {"text": "Moby-Dick de Herman Melville", "language": "es"},
    3: {"text": "Call me Ishmael.", "language": "en"},
    4: {"text": "Llámame Ismael.", "language": "es"},
    5: {"text": "Some years ago—never mind how long precisely—having little or no money in my purse, and nothing particular to interest me on shore, I thought I would sail about a little and see the watery part of the world.", "language": "en"},
    6: {"text": "Hace algunos años—no importa cuánto exactamente—, sin tener mucho o ningún dinero en mi bolsa, y sin nada que me interesara en tierra, pensé en navegar un poco y ver la parte acuática del mundo.", "language": "es"},
    7: {"text": "I embarked from the port of New Bedford.", "language": "en"},
    8: {"text": "Embarqué desde el puerto de New Bedford.", "language": "es"}
}


# Extraer el texto de la primera línea para el nombre del archivo de salida
output_file_name = text_to_speak[1]["text"].replace(" ", "_") + ".wav"
output_path = os.path.join("output", output_file_name)
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Inicializar lista para almacenar rutas de archivos y duraciones
audio_paths = []
video_paths = []

# Procesar cada entrada de texto
for i, entry in tqdm(text_to_speak.items(), desc="Generando archivos de audio", unit="file"):
    text = entry["text"]
    language = entry["language"]

    audio_path = os.path.join(cfg.TEMP_AUDIO_DIR, f"temp_{i}.wav")
    video_path = os.path.join(cfg.TEMP_VIDEO_DIR, f"temp_{i}.mp4")
    
    tts.tts_to_file(text=text, speaker_wav=SAMPLE_VOICE, language=language, file_path=audio_path)
    hvideo.generate_fragment(path_to_audio=audio_path, text=text, output_file=video_path)
    
    audio_paths.append(audio_path)
    video_paths.append(video_path)

# Cargar el audio de ruido blanco
white_noise = AudioSegment.from_mp3(WHITE_NOISE_FILE)

# Definir un segmento de silencio para agregar entre audios
silence = AudioSegment.silent(duration=SILENCE_DURATION)

# Concatenar ruido blanco con archivos de audio generados y agregar ruido blanco al final
combined = white_noise
for file_path in tqdm(audio_paths, desc="Concatenando archivos de audio", unit="file"):
    segment = AudioSegment.from_wav(file_path)
    combined += segment + silence

# Agregar ruido blanco al final
combined += white_noise

# Guardar el archivo de salida final
combined.export(output_path, format="wav")


# Combine video fragments
hvideo.combine_video_fragments(video_paths, output_path.replace('.wav', '.mp4'))

# Limpiar archivos temporales
'''for file_path in audio_paths:
    os.remove(file_path)
os.rmdir(temp_dir)

# Guardar las duraciones de texto
with open(f"{output_path}_text_timings.json", "w") as f:
    json.dump(durations, f, indent=4)

print(f"Archivos de audio generados y concatenados en {output_path}")
print("Duraciones de texto guardadas en text_timings.json")

gvideo.generate_video_with_text(output_path, f"{output_path.replace('.wav', '_text_timings.json')}", f"{output_path.replace('.wav', '.mp4')}")
'''