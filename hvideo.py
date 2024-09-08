from moviepy.editor import AudioFileClip, ColorClip, ImageClip, VideoFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import config as cfg


def generate_fragment(path_to_audio, text, output_file):
    font = ImageFont.truetype('arial.ttf', cfg.FONT_SIZE)
    image = Image.new('RGB', (cfg.WIDTH, cfg.HEIGHT), color=cfg.BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    lines = wrap_text(text, font, cfg.MAX_WIDTH)
    text_height = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines)
    y_offset = (cfg.HEIGHT - text_height) // 2

    for line in lines:
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        text_x = (cfg.WIDTH - text_width) / 2
        draw.text((text_x, y_offset), line, fill=cfg.TEXT_COLOR, font=font)
        y_offset += bbox[3] - bbox[1]

    image_array = np.array(image)
    audio_clip = AudioFileClip(path_to_audio)
    duration = audio_clip.duration
    image_clip = ImageClip(image_array, duration=duration)

    video_clip = image_clip.set_audio(audio_clip)
    video_clip.write_videofile(output_file, fps=cfg.FPS)

def wrap_text(text, font, max_width):
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

def combine_video_fragments(fragments, output_path):
    clips = []
    delay_duration = cfg.DURATION_BETWEEN_FRAGMENTS / 1000.0

    delay_clip = ColorClip(
        size=(cfg.WIDTH, cfg.HEIGHT), 
        color=cfg.BACKGROUND_COLOR,
        duration=delay_duration)

    for fragment in fragments:
        video_clip = VideoFileClip(fragment)
        clips.append(video_clip)
        clips.append(delay_clip)

    
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_path, fps=24)
