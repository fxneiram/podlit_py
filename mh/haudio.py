from pydub import AudioSegment
from tqdm import tqdm
import config as cfg


class AudioCombiner:
    def __init__(self, fragments, output_path, duration_between_fragments=None):
        self.fragments = fragments
        self.output_path = output_path
        self.duration_between_fragments = duration_between_fragments or cfg.DURATION_BETWEEN_FRAGMENTS

    def combine_audio_fragments(self):
        silence = AudioSegment.silent(duration=self.duration_between_fragments)
        combined = silence

        for file_path in tqdm(self.fragments, desc="Joining audio fragments.", unit="file"):
            segment = AudioSegment.from_wav(file_path)
            combined += segment + silence

        combined += silence

        combined.export(self.output_path, format="wav")
        print(f"Combined audio exported to: {self.output_path}")
