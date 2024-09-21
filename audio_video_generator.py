import os
import time

from TTS.api import TTS
from pkg import config as cfg
from fh.hvideo import VideoManager
from fh.haudio import AudioManager
from fh.hfiles import FileManager

import logging
import warnings

warnings.filterwarnings("ignore")
logging.getLogger("moviepy").setLevel(logging.ERROR)


class AudioVideoGenerator:
    def __init__(self, sample_voice, model_path, device="cpu"):
        self.sample_voice = sample_voice
        self.device = device
        self.tts = TTS(model_path, progress_bar=False).to(self.device)
        self.audio_manager = AudioManager()

        self.video_generator = VideoManager()

        self.file_manager = FileManager()

    def generate_files(self, text_to_speak, progress_callback=None) -> (str, str):
        task_path = self.file_manager.generate_random_path()

        self.file_manager.create_work_folders(task_path)

        output_audio_path, output_video_path = self.file_manager.get_final_file_names(text_to_speak[1]["text"])

        audio_paths = []
        video_paths = []

        total_files = len(text_to_speak)
        for i, (key, entry) in enumerate(text_to_speak.items()):
            language = entry["language"]
            text = entry["text"]
            if text[-1] == ".":
                text = text[:-1]

            audio_path = os.path.join(cfg.TEMP_AUDIO_DIR, task_path, f"temp_{i}.wav")
            video_path = os.path.join(cfg.TEMP_VIDEO_DIR, task_path, f"temp_{i}.mp4")

            self.tts.tts_to_file(text=text, speaker_wav=self.sample_voice, language=language, file_path=audio_path)
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
        self.video_generator.combine_video_fragments(video_paths, output_video_path)

        progress_callback(100, "Done")

        while True:
            try:
                ##self.file_manager.clean_temp_folders(task_path)
                time.sleep(10)
                break
            except Exception as e:
                print(f"Error cleaning temp folders, trying again in 10 seconds: {e}")
        
        return output_audio_path, output_video_path
    
    def combine_queue(self, tasks=None):
        if tasks is None:
            tasks = []

        audio_paths = []
        video_paths = []
        
        for task in tasks:
            audio_path, video_path = task
            audio_paths.append(audio_path)
            video_paths.append(video_path)

        filename = audio_paths[0].replace('.wav', '_mix_')
        output_audio_path = f'{filename}.wav'
        output_video_path = f'{filename}.mp4'

        self.audio_manager.combine_audio_fragments(audio_paths, output_audio_path)
        self.video_generator.combine_video_fragments(video_paths, output_video_path)
