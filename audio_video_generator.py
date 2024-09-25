import os
import time

from TTS.api import TTS
from pkg import config as cfg
from fh.hvideo import VideoManager
from fh.haudio import AudioManager
from fh.hfiles import FileManager

import torch

import logging
import warnings

warnings.filterwarnings("ignore")
logging.getLogger("moviepy").setLevel(logging.ERROR)


class AudioVideoGenerator:
    def __init__(self, selected_voice=None):
        self.selected_voice = selected_voice
        self.available_voices = []
        self.load_voices()

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_path = "tts_models/multilingual/multi-dataset/xtts_v2"
        self.tts = TTS(model_path, progress_bar=False).to(device)

        self.audio_manager = AudioManager()
        self.video_generator = VideoManager()
        self.file_manager = FileManager()

    def generate_files(self, text_to_speak, progress_callback=None) -> (str, str):
        start_time = time.time()

        task_path = self.file_manager.generate_random_path()
        self.file_manager.create_work_folders()
        output_audio_path, output_video_path = self.file_manager.get_final_file_names(text_to_speak[1]["text"])

        audio_paths = []
        video_paths = []

        total_files = len(text_to_speak)
        for i, (key, entry) in enumerate(text_to_speak.items()):
            language = entry["language"]
            text = entry["text"]
            if text[-1] == ".":
                text = text[:-1]

            audio_path = os.path.join(cfg.TEMP_DIR, f"{task_path}_tmp_{i}_a.wav")
            video_path = os.path.join(cfg.TEMP_DIR, f"{task_path}_tmp_{i}_v.mp4")

            self.tts.tts_to_file(text=text, speaker_wav=self.selected_voice, language=language, file_path=audio_path)
            self.audio_manager.add_silence(audio_path, 250, fps=24, before=True, after=True)

            self.video_generator.generate_fragment(path_to_audio=audio_path, text=text, output_file=video_path)

            audio_paths.append(audio_path)
            video_paths.append(video_path)

            if progress_callback:
                progress = (i + 1) / total_files * 100
                progress_callback(progress, f"Processing fragment {i + 1}/{total_files}")

        progress_callback(100, "Combining audio fragments")
        self.audio_manager.combine_audio_fragments(audio_paths, output_audio_path)

        progress_callback(100, "Combining video fragments")
        self.video_generator.combine_video_fragments_ffmpeg(video_paths, output_video_path)

        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)

        progress_callback(100, f"Done Elapsed {int(minutes)} minutes: {int(seconds)} seconds")

        while True:
            try:
                self.file_manager.clean_temp_folders()
                time.sleep(10)
                break
            except Exception as e:
                print(f"Error cleaning temp folders, trying again in 10 seconds: {e}")
        
        return output_audio_path, output_video_path
    
    def load_voices(self):
        self.available_voices = []
        for file in os.listdir("sample_voices"):
            if file.endswith(".wav"):
                self.available_voices.append(file)

        return self.available_voices

    def change_voice(self, voice):
        self.selected_voice = f"sample_voices/{voice}"

    def combine_queue(self, tasks=None, file_name=""):
        if len(tasks) < 1:
            return

        audio_paths = []
        video_paths = []
        
        for task in tasks:
            audio_path, video_path = task
            audio_paths.append(audio_path)
            video_paths.append(video_path)

        if file_name == "":
            output_audio_path = audio_paths[0].replace('.wav', '_mix_.wav')
            output_video_path = output_audio_path.replace('.wav', '.mp4')
        else:
            output_audio_path = file_name.replace('.mp4', '.wav')
            output_video_path = file_name

        self.audio_manager.combine_audio_fragments(audio_paths, output_audio_path)
        self.video_generator.combine_video_fragments_ffmpeg(video_paths, output_video_path)
