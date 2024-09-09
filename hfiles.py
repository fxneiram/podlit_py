import os
import config as cfg

def create_work_folders():
    os.makedirs(cfg.TEMP_AUDIO_DIR, exist_ok=True)
    os.makedirs(cfg.TEMP_VIDEO_DIR, exist_ok=True)
    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

def clean_temp_folders():
    for file_path in os.listdir(cfg.TEMP_AUDIO_DIR):
        os.remove(os.path.join(cfg.TEMP_AUDIO_DIR, file_path))
    
    for file_path in os.listdir(cfg.TEMP_VIDEO_DIR):
        os.remove(os.path.join(cfg.TEMP_VIDEO_DIR, file_path))
    
    os.rmdir(cfg.TEMP_AUDIO_DIR)
    os.rmdir(cfg.TEMP_VIDEO_DIR)

def get_final_file_names(title: str):
    audio_file_name = title.replace(" ", "_") + ".wav"
    video_file_name = title.replace(" ", "_") + ".mp4"
    audio_path = os.path.join(cfg.OUTPUT_DIR, audio_file_name)
    video_path = os.path.join(cfg.OUTPUT_DIR, video_file_name)
    return audio_path, video_path