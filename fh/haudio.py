import subprocess

from pydub import AudioSegment
from tqdm import tqdm
from pkg import config as cfg


class AudioManager:
    def __init__(self):
        pass

    def combine_audio_fragments(self, fragments, output_path):
        silence = AudioSegment.silent(duration=cfg.DURATION_BETWEEN_FRAGMENTS)
        combined = silence

        for file_path in fragments:
            segment = AudioSegment.from_wav(file_path)
            combined += segment + silence

        combined.export(output_path, format="wav")
        print(f"Combined audio exported to: {output_path}")

    def add_silence(self, audio_path, duration, fps, before=True, after=True):
        audio = AudioSegment.from_wav(audio_path)
        silence = AudioSegment.silent(duration=duration)

        if before:
            audio = silence + audio

        if after:
            audio = audio + silence

        current_duration_ms = len(audio)
        frame_duration_ms = 1000 / fps

        remainder = current_duration_ms % frame_duration_ms
        if remainder != 0:
            additional_silence = frame_duration_ms - remainder
            audio += AudioSegment.silent(duration=additional_silence)

        audio.export(audio_path, format="wav")
