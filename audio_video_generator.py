import logging
import os
import time
import warnings

from application.ports.tts_port import TextToSpeechPort
from fh.haudio import AudioManager
from fh.hfiles import FileManager
from fh.hvideo import VideoManager
from pkg import config as cfg

warnings.filterwarnings("ignore")
logging.getLogger("moviepy").setLevel(logging.ERROR)


class AudioVideoGenerator:
    def __init__(self, tts_engine: TextToSpeechPort, selected_voice=None, speech_speed=1.0):
        self.tts_engine = tts_engine
        self.selected_voice = selected_voice
        self.available_voices: list[str] = []
        self.speech_speed = speech_speed  # Velocidad del habla (1.0 = normal, <1.0 más lento, >1.0 más rápido)
        self.load_voices()

        self.audio_manager = AudioManager()
        self.video_generator = VideoManager()
        self.file_manager = FileManager()

    def set_speech_speed(self, speed):
        """Establece la velocidad del habla.

        Args:
            speed (float): Velocidad del habla.
                          1.0 = velocidad normal
                          <1.0 = más lento (ej: 0.8 para 80% de la velocidad normal)
                          >1.0 = más rápido (ej: 1.5 para 150% de la velocidad normal)
        """
        self.speech_speed = max(0.1, min(3.0, speed))  # Limitar entre 0.1 y 3.0 para evitar valores extremos

    def _prepare_text(self, text):
        # Remove trailing dots
        text = text.endswith(".") and text[:-1] or text
        return text

    def generate_files(self, text_to_speak, progress_callback=None) -> tuple[str, str]:
        start_time = time.time()

        task_path = self.file_manager.generate_random_path()
        self.file_manager.create_work_folders()
        # Get the first value from the text_to_speak dictionary
        first_key = next(iter(text_to_speak))
        output_audio_path, output_video_path = self.file_manager.get_final_file_names(text_to_speak[first_key]["text"])

        audio_paths = []
        video_paths = []

        total_files = len(text_to_speak)
        for i, (key, entry) in enumerate(text_to_speak.items()):
            language = entry["language"]
            text = entry["text"]
            text = self._prepare_text(text)

            audio_path = os.path.join(cfg.TEMP_DIR, f"{task_path}_tmp_{i}_a.wav")
            video_path = os.path.join(cfg.TEMP_DIR, f"{task_path}_tmp_{i}_v.mp4")

            self.tts_engine.synthesize(
                content=text,
                language=language,
                voice=self.selected_voice,
                speed=self.speech_speed,
                output_path=audio_path,
            )
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
        self.available_voices = self.tts_engine.list_voices()
        return self.available_voices

    def change_voice(self, voice):
        self.selected_voice = voice

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
            output_audio_path = audio_paths[0].replace(".wav", "_mix_.wav")
            output_video_path = output_audio_path.replace(".wav", ".mp4")
        else:
            output_audio_path = file_name.replace(".mp4", ".wav")
            output_video_path = file_name

        self.audio_manager.combine_audio_fragments(audio_paths, output_audio_path)
        self.video_generator.combine_video_fragments_ffmpeg(video_paths, output_video_path)
