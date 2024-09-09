from pydub import AudioSegment
import config as cfg
from tqdm import tqdm


def combine_audio_fragments(fragments, output_path):
    silence = AudioSegment.silent(duration=cfg.DURATION_BETWEEN_FRAGMENTS)

    combined = silence
    for file_path in tqdm(fragments, desc="Concatenando archivos de audio", unit="file"):
        segment = AudioSegment.from_wav(file_path)
        combined += segment + silence

    combined += silence
    combined.export(output_path, format="wav")