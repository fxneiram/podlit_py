import torch
from TTS.api import TTS
from tqdm import tqdm
import os
import config as cfg
import hvideo
import haudio
import hfiles

SAMPLE_VOICE = "sample_voices/faver_1.wav"

# Instance TTS model
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)

hfiles.create_work_folders()

# Texto a pronunciar
text_to_speak = {
    1: {"text": "Moby-Dick by Herman Melville", "language": "en"},
    2: {"text": "Moby-Dick de Herman Melville", "language": "es"},
    3: {"text": "Call me Ishmael.", "language": "en"},
    4: {"text": "Llámame Ismael.", "language": "es"},
}


# Extraer el texto de la primera línea para el nombre del archivo de salida
output_audio_path, output_video_path = hfiles.get_final_file_names(text_to_speak[1]["text"])

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

# Final files
haudio.combine_audio_fragments(audio_paths, output_audio_path)
hvideo.combine_video_fragments(video_paths, output_audio_path.replace('.wav', '.mp4'))

# Limpiar archivos temporales
hfiles.clean_temp_folders()