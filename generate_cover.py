"""Generate a 16:9 cover image for the AMD Hackathon submission."""
from PIL import Image, ImageDraw, ImageFont
import os

WIDTH, HEIGHT = 1920, 1080

# Dark gradient background
img = Image.new("RGB", (WIDTH, HEIGHT), "#0a0a0f")
draw = ImageDraw.Draw(img)

# Draw a subtle gradient rectangle
for y in range(HEIGHT):
    r = int(10 + (y / HEIGHT) * 25)
    g = int(10 + (y / HEIGHT) * 20)
    b = int(15 + (y / HEIGHT) * 45)
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

# Accent bars
draw.rectangle([0, 0, WIDTH, 12], fill="#e31937")  # AMD red top bar
draw.rectangle([0, HEIGHT - 12, WIDTH, HEIGHT], fill="#e31937")  # AMD red bottom bar

# Try to load fonts, fall back to default if not available
font_paths = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/calibri.ttf",
]

def load_font(size):
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

title_font = load_font(96)
subtitle_font = load_font(48)
body_font = load_font(36)
small_font = load_font(28)

# Title
title = "Style-Aware Vision Caption Agent"
subtitle = "AMD Developer Hackathon — Track 2: Video Captioning"
body = "Four stylistic captions from a two-step vision pipeline"
footer = "Fireworks AI · MiniMax M3 · Kimi K2P6 · Docker · linux/amd64"

# Center text horizontally
def text_size(text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

tw, th = text_size(title, title_font)
draw.text(((WIDTH - tw) // 2, 340), title, font=title_font, fill="#ffffff")

tw, th = text_size(subtitle, subtitle_font)
draw.text(((WIDTH - tw) // 2, 490), subtitle, font=subtitle_font, fill="#cccccc")

tw, th = text_size(body, body_font)
draw.text(((WIDTH - tw) // 2, 580), body, font=body_font, fill="#aaaaaa")

# Decorative line
draw.rectangle([(WIDTH // 2 - 200, 660), (WIDTH // 2 + 200, 668)], fill="#e31937")

# Footer
tw, th = text_size(footer, small_font)
draw.text(((WIDTH - tw) // 2, 900), footer, font=small_font, fill="#888888")

output_path = "C:/Users/Admin/amd-track2-agent-v2/submission_cover.png"
img.save(output_path, "PNG")
print(f"Cover saved to {output_path} ({WIDTH}x{HEIGHT})")
