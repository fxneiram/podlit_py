# Manual

## Installation
https://stackoverflow.com/questions/66726331/how-can-i-run-mozilla-tts-coqui-tts-training-with-cuda-on-a-windows-system
git clone https://github.com/coqui-ai/TTS
Download and install Python 3.8 (not 3.9+) for Windows. During the installation, ensure that you:
Opt to install it for all users.
Opt to add Python to the PATH.
Download and install CUDA Toolkit 10.1 (not 11.0+).
Download "cuDNN v7.6.5 (November 5th, 2019), for CUDA 10.1" (not cuDNN v8+), extract it, and then copy what's inside the cuda folder into C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v10.1.
Download the latest 64-bit version of eSpeak NG (no version constraints :-) ).
Download the latest 64-bit version of Git for Windows (no version constraints :-) ).
Open a PowerShell prompt to a folder where you'd like to install Coqui TTS.
Run git clone https://github.com/coqui-ai/TTS.git.
Run cd TTS.
Run python -m venv ..
Run .\Scripts\pip install -e ..
Run the following command (this differs from the command you get from the PyTorch website because of a known issue):
.\Scripts\pip install torch==1.8.0+cu101 torchvision==0.9.0+cu101 torchaudio===0.8.0 -f https://download.pytorch.org/whl/torch_stable.html
Put the following into a script called "test_cuda.py" in the TTS folder:

## Prompt
Genera un resumen del contenido de el capitulo 4 de politica para amador con la siguiente estructura:

1. El contenido debe alternar entre frases en inglés y español.
2. Cada frase debe estar en su idioma correspondiente, manteniendo el tono y el significado del texto original.
3. La salida debe tener la siguiente estructura de diccionario en Python, donde cada entrada contiene la clave, el texto, y el idioma.

python
{
    1: {"text": "Frase en inglés.", "language": "en"},
    2: {"text": "Frase en español.", "language": "es"},
    3: {"text": "Continua frase en inglés.", "language": "en"},
    4: {"text": "Continua frase en español.", "language": "es"},
    ...
}

4. La linea 1 debe ser el título en inglés seguido del autor y el capitulo, la linea 2, el título en español, seguido  autor y capitulo, ejemplo: 1: {"text": "_Book Name_ by _Author_, _Chapter Number_", "language": "en"},
5. El texto debe ser en prosa, y cada linea será una frase
5. Responde exclusivamente con el contenido json en texto plano sin añadir más
6. El total de lineas debe ser 50