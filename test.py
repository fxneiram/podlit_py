import torch
from TTS.api import TTS
from pydub import AudioSegment
from tqdm import tqdm
import os

SAMPLE_VOICE = "sample_voices/faver_1.wav"
WHITE_NOISE_FILE = "white_noise"

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

# List available 🐸TTS models
print(TTS().list_models())

# Init TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)

# Directory for temporary audio files
temp_dir = "temp_audio_files"
os.makedirs(temp_dir, exist_ok=True)

# Your text to speak
text_to_speak = {
    1: {"text": "The 48 Laws of Power by Robert Greene", "language": "en"},
    2: {"text": "Las 48 Leyes del Poder de Robert Greene", "language": "es"},
    3: {"text": "Never outshine the master.", "language": "en"},
    4: {"text": "Nunca eclipses al maestro.", "language": "es"},
    5: {"text": "Never put too much trust in friends, learn how to use enemies.", "language": "en"},
    6: {"text": "Nunca confíes demasiado en los amigos, aprende a utilizar a los enemigos.", "language": "es"},
    7: {"text": "Conceal your intentions.", "language": "en"},
    8: {"text": "Oculta tus intenciones.", "language": "es"},
    9: {"text": "Always say less than necessary.", "language": "en"},
    10: {"text": "Siempre di menos de lo necesario.", "language": "es"},
    11: {"text": "So much depends on reputation – guard it with your life.", "language": "en"},
    12: {"text": "Mucho depende de la reputación; protéjela con tu vida.", "language": "es"},
    13: {"text": "Court attention at all costs.", "language": "en"},
    14: {"text": "Busca la atención a toda costa.", "language": "es"},
    15: {"text": "Crush your enemy totally.", "language": "en"},
    16: {"text": "Destruye a tu enemigo por completo.", "language": "es"},
    17: {"text": "Use absence to increase respect and honor.", "language": "en"},
    18: {"text": "Usa la ausencia para aumentar el respeto y el honor.", "language": "es"},
    19: {"text": "Keep others in suspended terror: cultivate an air of unpredictability.", "language": "en"},
    20: {"text": "Mantén a los demás en terror suspendido: cultiva un aire de impredecibilidad.", "language": "es"},
    21: {"text": "Do not build fortresses to protect yourself – isolation is dangerous.", "language": "en"},
    22: {"text": "No construyas fortalezas para protegerte: el aislamiento es peligroso.", "language": "es"},
    23: {"text": "Know who you’re dealing with – do not offend the wrong person.", "language": "en"},
    24: {"text": "Sabe con quién estás tratando: no ofendas a la persona equivocada.", "language": "es"},
    25: {"text": "Play a sucker to catch a sucker – seem dumber than your mark.", "language": "en"},
    26: {"text": "Hazte el tonto para atrapar al tonto: parece más tonto que tu objetivo.", "language": "es"},
    27: {"text": "Use the surrender tactic: transform weakness into power.", "language": "en"},
    28: {"text": "Usa la táctica de rendición: transforma la debilidad en poder.", "language": "es"},
    29: {"text": "Concentrate your forces.", "language": "en"},
    30: {"text": "Concentra tus fuerzas.", "language": "es"},
    31: {"text": "Play to people’s fantasies.", "language": "en"},
    32: {"text": "Juega con las fantasías de la gente.", "language": "es"},
    33: {"text": "Discover each man’s thumbscrew.", "language": "en"},
    34: {"text": "Descubre el punto débil de cada persona.", "language": "es"},
    35: {"text": "Master the art of timing.", "language": "en"},
    36: {"text": "Domina el arte del tiempo.", "language": "es"},
    37: {"text": "Disdain things you cannot have: ignoring them is the best revenge.", "language": "en"},
    38: {"text": "Desprecia las cosas que no puedes tener: ignorarlas es la mejor venganza.", "language": "es"},
    39: {"text": "Stir up waters to catch fish.", "language": "en"},
    40: {"text": "Agita las aguas para pescar.", "language": "es"},
    41: {"text": "Avoid stepping into a great man’s shoes.", "language": "en"},
    42: {"text": "Evita ponerte en los zapatos de un gran hombre.", "language": "es"},
    43: {"text": "Strike the shepherd and the sheep will scatter.", "language": "en"},
    44: {"text": "Ataca al pastor y las ovejas se dispersarán.", "language": "es"},
    45: {"text": "Work on the hearts and minds of others.", "language": "en"},
    46: {"text": "Trabaja en los corazones y mentes de los demás.", "language": "es"},
    47: {"text": "Play the game of power.", "language": "en"},
    48: {"text": "Juega el juego del poder.", "language": "es"},
    49: {"text": "Never outshine the master.", "language": "en"},
    50: {"text": "Nunca eclipses al maestro.", "language": "es"},
    51: {"text": "Never put too much trust in friends, learn how to use enemies.", "language": "en"},
    52: {"text": "Nunca confíes demasiado en los amigos, aprende a utilizar a los enemigos.", "language": "es"},
    53: {"text": "Conceal your intentions.", "language": "en"},
    54: {"text": "Oculta tus intenciones.", "language": "es"},
    55: {"text": "Always say less than necessary.", "language": "en"},
    56: {"text": "Siempre di menos de lo necesario.", "language": "es"},
    57: {"text": "So much depends on reputation – guard it with your life.", "language": "en"},
    58: {"text": "Mucho depende de la reputación; protéjela con tu vida.", "language": "es"},
    59: {"text": "Court attention at all costs.", "language": "en"},
    60: {"text": "Busca la atención a toda costa.", "language": "es"},
    61: {"text": "Crush your enemy totally.", "language": "en"},
    62: {"text": "Destruye a tu enemigo por completo.", "language": "es"},
    63: {"text": "Use absence to increase respect and honor.", "language": "en"},
    64: {"text": "Usa la ausencia para aumentar el respeto y el honor.", "language": "es"},
    65: {"text": "Keep others in suspended terror: cultivate an air of unpredictability.", "language": "en"},
    66: {"text": "Mantén a los demás en terror suspendido: cultiva un aire de impredecibilidad.", "language": "es"},
    67: {"text": "Do not build fortresses to protect yourself – isolation is dangerous.", "language": "en"},
    68: {"text": "No construyas fortalezas para protegerte: el aislamiento es peligroso.", "language": "es"},
    69: {"text": "Know who you’re dealing with – do not offend the wrong person.", "language": "en"},
    70: {"text": "Sabe con quién estás tratando: no ofendas a la persona equivocada.", "language": "es"},
    71: {"text": "Play a sucker to catch a sucker – seem dumber than your mark.", "language": "en"},
    72: {"text": "Hazte el tonto para atrapar al tonto: parece más tonto que tu objetivo.", "language": "es"},
    73: {"text": "Use the surrender tactic: transform weakness into power.", "language": "en"},
    74: {"text": "Usa la táctica de rendición: transforma la debilidad en poder.", "language": "es"},
    75: {"text": "Concentrate your forces.", "language": "en"},
    76: {"text": "Concentra tus fuerzas.", "language": "es"},
    77: {"text": "Play to people’s fantasies.", "language": "en"},
    78: {"text": "Juega con las fantasías de la gente.", "language": "es"},
    79: {"text": "Discover each man’s thumbscrew.", "language": "en"},
    80: {"text": "Descubre el punto débil de cada persona.", "language": "es"},
    81: {"text": "Master the art of timing.", "language": "en"},
    82: {"text": "Domina el arte del tiempo.", "language": "es"},
    83: {"text": "Disdain things you cannot have: ignoring them is the best revenge.", "language": "en"},
    84: {"text": "Desprecia las cosas que no puedes tener: ignorarlas es la mejor venganza.", "language": "es"},
    85: {"text": "Stir up waters to catch fish.", "language": "en"},
    86: {"text": "Agita las aguas para pescar.", "language": "es"},
    87: {"text": "Avoid stepping into a great man’s shoes.", "language": "en"},
    88: {"text": "Evita ponerte en los zapatos de un gran hombre.", "language": "es"},
    89: {"text": "Strike the shepherd and the sheep will scatter.", "language": "en"},
    90: {"text": "Ataca al pastor y las ovejas se dispersarán.", "language": "es"},
    91: {"text": "Work on the hearts and minds of others.", "language": "en"},
    92: {"text": "Trabaja en los corazones y mentes de los demás.", "language": "es"},
    93: {"text": "Play the game of power.", "language": "en"},
    94: {"text": "Juega el juego del poder.", "language": "es"},
}

# Extract the text from the first line for the output file name
output_file_name = text_to_speak[1]["text"].replace(" ", "_") + ".wav"
output_path = os.path.join("output", output_file_name)
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Process each text entry
file_paths = []
for i, entry in tqdm(text_to_speak.items(), desc="Generating audio files", unit="file"):
    text = entry["text"]
    language = entry["language"]
    file_path = os.path.join(temp_dir, f"temp_{i}.wav")
    
    tts.tts_to_file(text=text, speaker_wav=SAMPLE_VOICE, language=language, file_path=file_path)
    
    file_paths.append(file_path)

# Load the white noise audio
white_noise = AudioSegment.from_mp3(WHITE_NOISE_FILE)

# Define a silent segment to add between audios
silence_duration = 500  # 500 ms of silence
silence = AudioSegment.silent(duration=silence_duration)

# Concatenate white noise with generated audio files and add white noise at the end
combined = white_noise
for file_path in tqdm(file_paths, desc="Concatenating audio files", unit="file"):
    segment = AudioSegment.from_wav(file_path)
    combined += segment + silence

# Add white noise at the end
combined += white_noise

# Save the final output
combined.export(output_path, format="wav")

# Clean up temporary files
for file_path in file_paths:
    os.remove(file_path)
os.rmdir(temp_dir)

print(f"Audio files generated and concatenated into {output_path}")
