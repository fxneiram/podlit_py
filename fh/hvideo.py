from moviepy.editor import AudioFileClip, ColorClip, ImageClip, VideoFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pkg import config as cfg


class VideoManager:
    def __init__(self, width=cfg.WIDTH, height=cfg.HEIGHT, font_size=cfg.FONT_SIZE,
                 background_color=cfg.BACKGROUND_COLOR, text_color=cfg.TEXT_COLOR,
                 fps=cfg.FPS, duration_between_fragments=cfg.DURATION_BETWEEN_FRAGMENTS):

        self.width = width
        self.height = height
        self.font_size = font_size
        self.background_color = background_color
        self.text_color = text_color
        self.fps = fps
        self.duration_between_fragments = duration_between_fragments
        self.font = ImageFont.truetype('arial.ttf', self.font_size)

    def generate_fragment(self, path_to_audio, text, output_file):
        image = Image.new('RGB', (self.width, self.height), color=self.background_color)
        draw = ImageDraw.Draw(image)

        lines = self.wrap_text(text, self.font, cfg.MAX_WIDTH)
        text_height = sum(self.font.getbbox(line)[3] - self.font.getbbox(line)[1] for line in lines)
        y_offset = (self.height - text_height) // 2

        for line in lines:
            bbox = self.font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_x = (self.width - text_width) / 2
            draw.text((text_x, y_offset), line, fill=self.text_color, font=self.font)
            y_offset += bbox[3] - bbox[1]

        image_array = np.array(image)

        audio_clip = AudioFileClip(path_to_audio)
        duration = audio_clip.duration
        image_clip = ImageClip(image_array, duration=duration)

        video_clip = image_clip.set_audio(audio_clip)
        video_clip.write_videofile(output_file, fps=self.fps)

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
        clips = []
        delay_duration = self.duration_between_fragments / 1000.0

        delay_clip = ColorClip(size=(self.width, self.height), color=self.background_color, duration=delay_duration)
        clips.append(delay_clip)

        for fragment in fragments:
            video_clip = VideoFileClip(fragment)
            clips.append(video_clip)
            clips.append(delay_clip)

        final_clip = concatenate_videoclips(clips, method="chain")
        final_clip.write_videofile(output_path, fps=24)

