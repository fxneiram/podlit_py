import os
from pkg import config as cfg


class FileManager:
    def __init__(self, temp_audio_dir=cfg.TEMP_AUDIO_DIR, temp_video_dir=cfg.TEMP_VIDEO_DIR, output_dir=cfg.OUTPUT_DIR):
        self.temp_audio_dir = temp_audio_dir
        self.temp_video_dir = temp_video_dir
        self.output_dir = output_dir

    def create_work_folders(self):
        os.makedirs(self.temp_audio_dir, exist_ok=True)
        os.makedirs(self.temp_video_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def clean_temp_folders(self):
        self._clean_folder(self.temp_audio_dir)
        self._clean_folder(self.temp_video_dir)

    def _clean_folder(self, folder_path):
        for file_path in os.listdir(folder_path):
            os.remove(os.path.join(folder_path, file_path))
        os.rmdir(folder_path)

    def get_final_file_names(self, title: str):
        audio_file_name = title.replace(" ", "_") + ".wav"
        video_file_name = title.replace(" ", "_") + ".mp4"
        audio_path = os.path.join(self.output_dir, audio_file_name)
        video_path = os.path.join(self.output_dir, video_file_name)
        return audio_path, video_path
