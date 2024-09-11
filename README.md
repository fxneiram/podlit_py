# PodLitPy

## Description

I created this project to generate multimedia content for practicing my English. The main idea is to use a tool like ChatGPT with the prompt provided below. The generated content can be summaries of books or any other topic that the user finds relevant and enjoyable. The output is produced in both audio (WAV) and video (MP4) formats, making it easier to listen and learn in English.

## Built with

This project was built using:

- **Python**: The main programming language used for the project.
- **Torch (PyTorch)**: For handling deep learning models, including text-to-speech processing.
- **TTS**: A text-to-speech library to convert text into spoken audio.
- **tqdm**: For visualizing the progress of audio and video generation.
- **os**: To manage file directories and paths.
- **Custom helper modules (hvideo, haudio, hfiles)**: For handling audio and video file creation, combination, and cleanup tasks.


## Installation
https://stackoverflow.com/questions/66726331/how-can-i-run-mozilla-tts-coqui-tts-training-with-cuda-on-a-windows-system
1. Clone next repository in root of PodLitPy project
```shell
git clone https://github.com/coqui-ai/TTS
```
2. [Download](https://developer.nvidia.com/cuda-10.1-download-archive-base) and install CUDA Toolkit 10.1 (not 11.0+)

3. [Download](https://developer.nvidia.com/rdp/cudnn-archive) "cuDNN v7.6.5 (November 5th, 2019), for CUDA 10.1" (not cuDNN v8+), extract it, and then copy what's inside the `cuda` folder into `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v10.1`.

4. [Download](https://github.com/espeak-ng/espeak-ng/releases) the latest 64-bit version of eSpeak NG (no version constraints :-).

5. Consider using a virtual environment, such as `venv` or a tool like `Anaconda3` (optional).

6. Run next command
```shell
.\Scripts\pip install -e
```

7. Run next command
```shell
.\Scripts\pip install torch==1.8.0+cu101 torchvision==0.9.0+cu101 torchaudio===0.8.0 -f https://download.pytorch.org/whl/torch_stable.html
```
## Prompt
Feel free to adjust the following prompt according to your needs, but make sure to maintain the output format as specified in the base prompt.
```
Generate a summary of the content of Chapter 4 of *Politics for Amador* with the following structure:

1. The content should alternate between sentences in English and Spanish.
2. Each sentence should be in its corresponding language, maintaining the tone and meaning of the original text.
3. The output should have the following Python dictionary structure, where each entry contains the key, the text, and the language.

```python
{
    1: {"text": "Sentence in English.", "language": "en"},
    2: {"text": "Sentence in Spanish.", "language": "es"},
    3: {"text": "Continued sentence in English.", "language": "en"},
    4: {"text": "Continued sentence in Spanish.", "language": "es"},
    ...
}
```
4. Line 1 should be the title in English followed by the author and chapter number, and line 2 should be the title in Spanish, followed by the author and chapter number. For example: 1: {"text": "Book Name by Author, Chapter Number", "language": "en"},
5. The text should be in prose, and each line will be a sentence.
6. Respond exclusively with the JSON content in plain text without adding anything else.
The total number of lines should be 50.
```
## How to use

To generate multimedia content, follow these steps:

1. Run next command
```shell
python main.py
```
2. Use the provided prompt and adjust it according to your needs.
3. Paste the result of the prompt into the PodLitPy job queue.
4. The project will generate WAV and MP4 files based on the provided prompt on the `output` folder.
5. Use the output files to practice and enhance your language skills by listening to the generated content in your preferred language.
6. If desired, you can upload the content to podcast platforms like [Spotify Podcasters](https://podcasters.spotify.com/), but remember to be mindful of copyrighted material
