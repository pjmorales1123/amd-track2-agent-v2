"""Generate a simple 3-slide PDF for the submission."""
from PIL import Image, ImageDraw, ImageFont
import os

WIDTH, HEIGHT = 1920, 1080

def load_font(size):
    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def new_slide():
    img = Image.new("RGB", (WIDTH, HEIGHT), "#0a0a0f")
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        r = int(10 + (y / HEIGHT) * 25)
        g = int(10 + (y / HEIGHT) * 20)
        b = int(15 + (y / HEIGHT) * 45)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    draw.rectangle([0, 0, WIDTH, 12], fill="#e31937")
    draw.rectangle([0, HEIGHT - 12, WIDTH, HEIGHT], fill="#e31937")
    return img, draw

def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def centered_text(draw, text, y, font, color="#ffffff"):
    w, h = text_size(draw, text, font)
    draw.text(((WIDTH - w) // 2, y), text, font=font, fill=color)

# Slide 1: cover
cover = Image.open("C:/Users/Admin/amd-track2-agent-v2/submission_cover.png")

# Slide 2: pipeline
img, draw = new_slide()
title_font = load_font(72)
body_font = load_font(42)
small_font = load_font(32)

centered_text(draw, "Pipeline", 200, title_font)
centered_text(draw, "1. Download clip & extract 3–6 scene-aware keyframes", 360, body_font, "#cccccc")
centered_text(draw, "2. MiniMax M3 writes a structured visual brief", 440, body_font, "#cccccc")
centered_text(draw, "3. MiniMax M3 verifies the brief against the frames", 520, body_font, "#cccccc")
centered_text(draw, "4. Kimi K2P6 generates four style captions sequentially", 600, body_font, "#cccccc")
centered_text(draw, "5. Keyword guardrails retry any weak style match", 680, body_font, "#cccccc")
slide2 = img

# Slide 3: submission details
img, draw = new_slide()
centered_text(draw, "Submission Details", 200, title_font)
centered_text(draw, "Docker Image:", 380, body_font, "#cccccc")
centered_text(draw, "pjmorales04/amd-track2-agent-v2:latest", 450, body_font, "#ffffff")
centered_text(draw, "Platform: linux/amd64", 540, body_font, "#cccccc")
centered_text(draw, "API: Fireworks AI (MiniMax M3 + Kimi K2P6)", 620, body_font, "#cccccc")
centered_text(draw, "GitHub: pjmorales1123/amd-track2-agent-v2", 700, body_font, "#cccccc")
slide3 = img

# Save as PDF
cover.save(
    "C:/Users/Admin/amd-track2-agent-v2/submission_slides.pdf",
    "PDF",
    resolution=100.0,
    save_all=True,
    append_images=[slide2, slide3],
)
print("PDF saved to C:/Users/Admin/amd-track2-agent-v2/submission_slides.pdf")
