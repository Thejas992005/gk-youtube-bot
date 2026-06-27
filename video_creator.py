from moviepy.editor import *
from moviepy.video.tools.drawing import color_gradient
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

# ── Config ──────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 720
FPS = 24
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_PATH_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Colors
BG_COLOR       = (15, 23, 42)      # Dark navy
ACCENT_COLOR   = (99, 102, 241)    # Indigo
QUESTION_COLOR = (255, 255, 255)   # White
OPTION_COLOR   = (226, 232, 240)   # Light gray
ANSWER_COLOR   = (52, 211, 153)    # Green
TIMER_COLOR    = (251, 191, 36)    # Yellow
TOPIC_COLOR    = (148, 163, 184)   # Muted blue-gray

def make_text_image(text, font_path, font_size, color, max_width=None, align="center"):
    """Render text to a PIL image with optional word wrap."""
    font = ImageFont.truetype(font_path, font_size)
    if max_width:
        # Estimate chars per line
        avg_char_w = font_size * 0.55
        chars_per_line = max(1, int(max_width / avg_char_w))
        lines = textwrap.wrap(text, width=chars_per_line)
    else:
        lines = [text]

    line_h = font_size + 8
    img_h = line_h * len(lines) + 10
    img_w = max_width if max_width else WIDTH

    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        if align == "center":
            x = (img_w - tw) // 2
        elif align == "left":
            x = 0
        else:
            x = img_w - tw
        draw.text((x, i * line_h), line, font=font, fill=color)

    return np.array(img)

def pil_to_clip(pil_arr, x, y, duration):
    """Convert a numpy RGBA array to a positioned MoviePy clip."""
    clip = ImageClip(pil_arr, ismask=False).set_duration(duration)
    clip = clip.set_position((x, y))
    return clip

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)

def create_background(duration):
    """Solid dark background clip."""
    bg = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    return ImageClip(np.array(bg)).set_duration(duration)

def create_header_bar(topic, duration):
    img = Image.new("RGBA", (WIDTH, 60), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([20, 5, WIDTH - 20, 55], radius=12, fill=(*ACCENT_COLOR, 200))
    font = ImageFont.truetype(FONT_PATH, 22)
    label = f"📚 GK Quiz  |  {topic}"
    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, 15), label, font=font, fill=(255, 255, 255, 255))
    return ImageClip(np.array(img), ismask=False).set_duration(duration).set_position((0, 10))

def create_question_phase(question_data, show_answer=False):
    """
    Returns a list of clips for one phase.
    show_answer=False → question + options
    show_answer=True  → question + options + highlighted answer
    """
    clips = []
    q_text  = question_data["question"]
    options = question_data["options"]
    answer  = question_data["answer"]

    # Question box
    q_img = Image.new("RGBA", (WIDTH - 80, 150), (0, 0, 0, 0))
    q_draw = ImageDraw.Draw(q_img)
    draw_rounded_rect(q_draw, [0, 0, WIDTH - 82, 148], 16, (30, 41, 59, 230))
    font_q = ImageFont.truetype(FONT_PATH, 26)
    wrapped = textwrap.wrap(q_text, width=62)
    for i, line in enumerate(wrapped[:4]):
        bbox = q_draw.textbbox((0, 0), line, font=font_q)
        tw = bbox[2] - bbox[0]
        q_draw.text(((WIDTH - 80 - tw) // 2, 15 + i * 34), line, font=font_q, fill=QUESTION_COLOR)

    clips.append(ImageClip(np.array(q_img), ismask=False).set_position((40, 90)))

    # Options
    opt_colors = {
        "A": (79, 70, 229),
        "B": (16, 185, 129),
        "C": (245, 158, 11),
        "D": (239, 68, 68),
    }
    opt_labels = list(options.keys())
    for idx, key in enumerate(opt_labels):
        col = idx % 2
        row = idx // 2
        ox = 50 + col * (WIDTH // 2)
        oy = 260 + row * 90

        o_img = Image.new("RGBA", (WIDTH // 2 - 70, 75), (0, 0, 0, 0))
        o_draw = ImageDraw.Draw(o_img)

        base_c = opt_colors[key]
        if show_answer and key == answer:
            fill = (*ANSWER_COLOR, 230)
            text_c = (0, 0, 0, 255)
        else:
            fill = (*base_c, 180)
            text_c = (255, 255, 255, 255)

        draw_rounded_rect(o_draw, [0, 0, WIDTH // 2 - 72, 73], 12, fill)

        font_o = ImageFont.truetype(FONT_PATH, 20)
        opt_text = f"{key}. {options[key]}"
        wrapped_o = textwrap.wrap(opt_text, width=32)
        for li, line in enumerate(wrapped_o[:2]):
            o_draw.text((14, 14 + li * 26), line, font=font_o, fill=text_c)

        clips.append(ImageClip(np.array(o_img), ismask=False).set_position((ox, oy)))

    if show_answer:
        exp_text = f"✅ Answer: {answer}  —  {question_data.get('explanation','')}"
        exp_img = Image.new("RGBA", (WIDTH - 80, 70), (0, 0, 0, 0))
        exp_draw = ImageDraw.Draw(exp_img)
        draw_rounded_rect(exp_draw, [0, 0, WIDTH - 82, 68], 12, (6, 78, 59, 220))
        font_e = ImageFont.truetype(FONT_PATH_REG, 19)
        wrapped_e = textwrap.wrap(exp_text, width=82)
        for li, line in enumerate(wrapped_e[:2]):
            exp_draw.text((14, 10 + li * 24), line, font=font_e, fill=(167, 243, 208, 255))
        clips.append(ImageClip(np.array(exp_img), ismask=False).set_position((40, 460)))

    return clips

def create_timer_clip(seconds_left, total, duration_per_frame=1/FPS):
    """Single timer frame."""
    img = Image.new("RGBA", (160, 80), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, 159, 79], radius=14, fill=(30, 41, 59, 220))
    pct = seconds_left / total
    bar_w = int(136 * pct)
    draw.rounded_rectangle([12, 52, 148, 66], radius=6, fill=(55, 65, 81, 255))
    bar_color = (52, 211, 153) if pct > 0.4 else (251, 191, 36) if pct > 0.2 else (239, 68, 68)
    if bar_w > 0:
        draw.rounded_rectangle([12, 52, 12 + bar_w, 66], radius=6, fill=(*bar_color, 255))
    font_t = ImageFont.truetype(FONT_PATH, 32)
    label = str(seconds_left)
    bbox = draw.textbbox((0, 0), label, font=font_t)
    tw = bbox[2] - bbox[0]
    draw.text(((160 - tw) // 2, 8), label, font=font_t, fill=(*bar_color, 255))
    return np.array(img)


def create_video(question_data, output_path="output.mp4"):
    """Assemble the full MCQ video."""
    QUESTION_DURATION = 8    # Show question + options
    COUNTDOWN_DURATION = 7   # Countdown timer
    ANSWER_DURATION = 8      # Show answer
    TOTAL = QUESTION_DURATION + COUNTDOWN_DURATION + ANSWER_DURATION

    topic = question_data.get("topic", "General Knowledge")
    all_clips = []
    bg = create_background(TOTAL)
    all_clips.append(bg)

    # ── Phase 1: Question (0 → QUESTION_DURATION) ──
    header = create_header_bar(topic, QUESTION_DURATION)
    all_clips.append(header)
    q_clips = create_question_phase(question_data, show_answer=False)
    for c in q_clips:
        all_clips.append(c.set_start(0).set_duration(QUESTION_DURATION))

    # ── Phase 2: Countdown (QUESTION_DURATION → QUESTION_DURATION+COUNTDOWN) ──
    header2 = create_header_bar(topic, COUNTDOWN_DURATION).set_start(QUESTION_DURATION)
    all_clips.append(header2)
    q_clips2 = create_question_phase(question_data, show_answer=False)
    for c in q_clips2:
        all_clips.append(c.set_start(QUESTION_DURATION).set_duration(COUNTDOWN_DURATION))

    timer_frames = []
    for s in range(COUNTDOWN_DURATION, 0, -1):
        frame = create_timer_clip(s, COUNTDOWN_DURATION)
        timer_frames.append(ImageClip(frame, ismask=False)
                            .set_duration(1)
                            .set_position((WIDTH - 180, HEIGHT - 110)))
    timer_seq = concatenate_videoclips(timer_frames).set_start(QUESTION_DURATION)
    all_clips.append(timer_seq)

    # ── Phase 3: Answer (QUESTION_DURATION+COUNTDOWN → TOTAL) ──
    ans_start = QUESTION_DURATION + COUNTDOWN_DURATION
    header3 = create_header_bar(topic, ANSWER_DURATION).set_start(ans_start)
    all_clips.append(header3)
    a_clips = create_question_phase(question_data, show_answer=True)
    for c in a_clips:
        all_clips.append(c.set_start(ans_start).set_duration(ANSWER_DURATION))

    final = CompositeVideoClip(all_clips, size=(WIDTH, HEIGHT))
    final.write_videofile(output_path, fps=FPS, codec="libx264",
                          audio=False, logger=None)
    print(f"✅ Video saved: {output_path}")
    return output_path


if __name__ == "__main__":
    sample = {
        "question": "Which planet is known as the Red Planet?",
        "options": {"A": "Earth", "B": "Mars", "C": "Jupiter", "D": "Venus"},
        "answer": "B",
        "explanation": "Mars appears red due to iron oxide (rust) on its surface.",
        "topic": "Space & Universe"
    }
    create_video(sample, "test_output.mp4")
