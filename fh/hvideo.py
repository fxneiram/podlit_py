import cv2
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
import wave
import contextlib


class VideoManager:
    def __init__(self, width=640, height=480, font_size=24, background_color=(0, 0, 0), text_color=(255, 255, 255),
                 fps=24):
        self.width = width
        self.height = height
        self.font_size = font_size
        self.background_color = background_color
        self.text_color = text_color
        self.fps = fps
        self.font = ImageFont.truetype('arial.ttf', self.font_size)

    def generate_fragment(self, path_to_audio, text, output_file):
        fragment_tmp = output_file.replace('.mp4', '.tmp')

        with contextlib.closing(wave.open(path_to_audio, 'r')) as audio_file:
            frames = audio_file.getnframes()
            rate = audio_file.getframerate()
            duration = frames / float(rate)

        image = Image.new('RGB', (self.width, self.height), color=self.background_color)
        draw = ImageDraw.Draw(image)

        lines = self.wrap_text(text, self.font, self.width)
        text_height = sum(self.font.getbbox(line)[3] - self.font.getbbox(line)[1] for line in lines)
        y_offset = (self.height - text_height) // 2

        for line in lines:
            bbox = self.font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_x = (self.width - text_width) / 2
            draw.text((text_x, y_offset), line, fill=self.text_color, font=self.font)
            y_offset += bbox[3] - bbox[1]

        image_array = np.array(image)

        print("Generating tmp video fragment...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec para MP4
        video = cv2.VideoWriter(output_file, fourcc, self.fps, (self.width, self.height))

        for _ in range(int(duration * self.fps)):
            video.write(cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR))

        video.release()

        os.rename(output_file, fragment_tmp)

        os.system(f"ffmpeg -i {fragment_tmp} -i {path_to_audio} -c:v copy -c:a aac -strict experimental {output_file}")
        os.remove(fragment_tmp)

    def wrap_text(self, text, font, max_width):
        lines = []
        words = text.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word

        if line:
            lines.append(line)
        return lines

    def combine_video_fragments(self, fragments, output_path):
        fragment_tmp = output_path.replace('.mp4', '.tmp')
        audio_file = output_path.replace('.mp4', '.wav')

        clips = [cv2.VideoCapture(fragment) for fragment in fragments]

        width = int(clips[0].get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(clips[0].get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = clips[0].get(cv2.CAP_PROP_FPS)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        for clip in clips:
            while True:
                ret, frame = clip.read()
                if not ret:
                    break
                out.write(frame)
            clip.release()

        out.release()

        os.rename(output_path, fragment_tmp)

        os.system(f"ffmpeg -i {fragment_tmp} -i {audio_file} -c:v copy -c:a aac -strict experimental {output_path}")
        os.remove(fragment_tmp)
