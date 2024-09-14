import os
from TTS.api import TTS
from tqdm import tqdm
import config as cfg
import hvideo
import haudio
import hfiles

import warnings
warnings.filterwarnings("ignore")

import logging
logging.getLogger("moviepy").setLevel(logging.ERROR)


class AudioVideoGenerator:
    def __init__(self, sample_voice, model_path, device="cpu"):
        self.sample_voice = sample_voice
        self.device = device
        self.tts = TTS(model_path, progress_bar=False).to(self.device)
    
    def generate_files(self, text_to_speak, progress_callback=None):
        hfiles.create_work_folders()
        
        output_audio_path, output_video_path = hfiles.get_final_file_names(text_to_speak[1]["text"])
        
        audio_paths = []
        video_paths = []

        total_files = len(text_to_speak)
        for i, (key, entry) in enumerate(text_to_speak.items()):
            language = entry["language"]
            text = entry["text"]
            if text[-1] == ".":
                text = text[:-1]

            audio_path = os.path.join(cfg.TEMP_AUDIO_DIR, f"temp_{i}.wav")
            video_path = os.path.join(cfg.TEMP_VIDEO_DIR, f"temp_{i}.mp4")

            self.tts.tts_to_file(text=text, speaker_wav=self.sample_voice, language=language, file_path=audio_path)
            hvideo.generate_fragment(path_to_audio=audio_path, text=text, output_file=video_path)

            audio_paths.append(audio_path)
            video_paths.append(video_path)

            if progress_callback:
                progress = (i + 1) / total_files * 100
                progress_callback(progress, f"Processing fragment {i + 1}/{total_files}")

        progress_callback(100, "Combining audio fragments")
        haudio.combine_audio_fragments(audio_paths, output_audio_path)
        
        progress_callback(100, "Combining video fragments")
        hvideo.combine_video_fragments(video_paths, output_audio_path.replace('.wav', '.mp4'))
        
        progress_callback(100, "Done")
        
        while True:
            try:
                hfiles.clean_temp_folders()
                time.sleep(10)
                break





