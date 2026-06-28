from moviepy.editor import *
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

# ── Config ──────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 720
FPS = 24

# Colors
BG_COLOR       = (15, 23, 42)
ACCENT_COLOR   = (99, 102, 241)
QUESTION_COLOR = (255, 255, 255)
OPTION_COLOR   = (226, 232, 240)
ANSWER_COLOR   = (52, 211, 153)
TIMER_COLOR    = (251, 191, 36)

def get_font(size):
    """Try multiple font paths, fall back to default."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    # Fall back to default PIL font
    return ImageFont.load_default()

def get_font_reg(size):
    """Regular (non-bold) font."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)

def create_frame(question_data, show_answer=False, countdown=None):
    """Create a single frame as numpy array."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    topic = question_data.get("topic", "General Knowledge")
    question = question_data["question"]
    options = question_data["options"]
    answer = question_data["answer"]

    # ── Header bar ──
    draw.rounded_rectangle([20, 10, WIDTH-20, 60], radius=12,
                           fill=(*ACCENT_COLOR, 255))
    font_h = get_font(22)
    label = f"GK Quiz  |  {topic}"
    bbox = draw.textbbox((0,0), label, font=font_h)
    tw = bbox[2]-bbox[0]
    draw.text(((WIDTH-tw)//2, 22), label, font=font_h, fill=(255,255,255))

    # ── Question box ──
    draw.rounded_rectangle([30, 75, WIDTH-30, 230], radius=14,
                           fill=(30, 41, 59))
    font_q = get_font(24)
    wrapped = textwrap.wrap(question, width=65)
    for i, line in enumerate(wrapped[:4]):
        bbox = draw.textbbox((0,0), line, font=font_q)
        tw = bbox[2]-bbox[0]
        draw.text(((WIDTH-tw)//2, 90 + i*36), line,
                  font=font_q, fill=QUESTION_COLOR)

    # ── Options ──
    opt_colors = {
        "A": (79, 70, 229),
        "B": (16, 185, 129),
        "C": (245, 158, 11),
        "D": (239, 68, 68),
    }
    for idx, (key, val) in enumerate(options.items()):
        col = idx % 2
        row = idx // 2
        ox = 40 + col * (WIDTH//2)
        oy = 245 + row * 100

        base_c = opt_colors.get(key, (100,100,100))
        if show_answer and key == answer:
            fill = ANSWER_COLOR
            text_c = (0, 0, 0)
        else:
            fill = base_c
            text_c = (255, 255, 255)

        draw.rounded_rectangle([ox, oy, ox + WIDTH//2 - 60, oy + 80],
                               radius=12, fill=fill)

        font_o = get_font(20)
        opt_text = f"{key}. {val}"
        wrapped_o = textwrap.wrap(opt_text, width=35)
        for li, line in enumerate(wrapped_o[:2]):
            draw.text((ox + 14, oy + 14 + li*26), line,
                     font=font_o, fill=text_c)

    # ── Countdown timer ──
    if countdown is not None:
        pct = countdown / 7
        bar_color = (52,211,153) if pct > 0.5 else (251,191,36) if pct > 0.25 else (239,68,68)
        draw.rounded_rectangle([WIDTH-190, HEIGHT-110, WIDTH-30, HEIGHT-30],
                               radius=14, fill=(30,41,59))
        draw.rounded_rectangle([WIDTH-178, HEIGHT-60, WIDTH-42, HEIGHT-46],
                               radius=6, fill=(55,65,81))
        bar_w = int(136 * pct)
        if bar_w > 0:
            draw.rounded_rectangle([WIDTH-178, HEIGHT-60,
                                   WIDTH-178+bar_w, HEIGHT-46],
                                  radius=6, fill=bar_color)
        font_t = get_font(36)
        num = str(countdown)
        bbox = draw.textbbox((0,0), num, font=font_t)
        tw = bbox[2]-bbox[0]
        cx = WIDTH - 110 - tw//2
        draw.text((cx, HEIGHT-105), num, font=font_t, fill=bar_color)

    # ── Answer explanation ──
    if show_answer:
        exp = f"Answer: {answer}  —  {question_data.get('explanation','')}"
        draw.rounded_rectangle([30, HEIGHT-110, WIDTH-30, HEIGHT-20],
                               radius=12, fill=(6,78,59))
        font_e = get_font_reg(18)
        wrapped_e = textwrap.wrap(exp, width=90)
        for li, line in enumerate(wrapped_e[:2]):
            draw.text((44, HEIGHT-100 + li*26), line,
                     font=font_e, fill=(167,243,208))

    return np.array(img)


def create_video(question_data, output_path="output.mp4"):
    QUESTION_DURATION = 8
    COUNTDOWN_DURATION = 7
    ANSWER_DURATION = 8
    TOTAL = QUESTION_DURATION + COUNTDOWN_DURATION + ANSWER_DURATION

    frames = []

    # Phase 1: Question (8 seconds)
    frame = create_frame(question_data, show_answer=False, countdown=None)
    for _ in range(QUESTION_DURATION * FPS):
        frames.append(frame)

    # Phase 2: Countdown (7 seconds)
    for s in range(COUNTDOWN_DURATION, 0, -1):
        frame = create_frame(question_data, show_answer=False, countdown=s)
        for _ in range(FPS):
            frames.append(frame)

    # Phase 3: Answer (8 seconds)
    frame = create_frame(question_data, show_answer=True, countdown=None)
    for _ in range(ANSWER_DURATION * FPS):
        frames.append(frame)

    print(f"🎞️  Rendering {len(frames)} frames...")
    clip = ImageSequenceClip(frames, fps=FPS)
    clip.write_videofile(output_path, codec="libx264",
                        audio=False, logger=None)
    print(f"✅ Video saved: {output_path}")
    return output_path


if __name__ == "__main__":
    sample = {
        "question": "Which planet is known as the Red Planet?",
        "options": {"A": "Earth", "B": "Mars", "C": "Jupiter", "D": "Venus"},
        "answer": "B",
        "explanation": "Mars appears red due to iron oxide on its surface.",
        "topic": "Space & Universe"
    }
    create_video(sample, "test_output.mp4")
