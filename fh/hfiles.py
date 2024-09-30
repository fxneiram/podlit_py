import os
import random
import string
import re
from pkg import config as cfg


class FileManager:
    def __init__(self, temp_dir=cfg.TEMP_DIR, output_dir=cfg.OUTPUT_DIR):
        self.temp_dir = temp_dir
        self.output_dir = output_dir

    def create_work_folders(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def clean_temp_folders(self):
        tmp = os.path.join(self.temp_dir)
        self._clean_folder(tmp)

    def _clean_folder(self, folder_path):
        for file_path in os.listdir(folder_path):
            os.remove(os.path.join(folder_path, file_path))
        os.rmdir(folder_path)

    def get_final_file_names(self, title: str):
        _title = self.sanitize_filename(title)
        audio_file_name = _title + ".wav"
        video_file_name = _title + ".mp4"
        audio_path = os.path.join(self.output_dir, audio_file_name)
        video_path = os.path.join(self.output_dir, video_file_name)
        return audio_path, video_path

    def generate_random_path(self, length=10):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def sanitize_filename(self, filename: str) -> str:
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename)
        sanitized = sanitized.replace(" ", "_")
        return sanitized
