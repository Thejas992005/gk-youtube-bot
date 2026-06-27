import os
import json
import time
import schedule
import logging
from datetime import datetime
from question_generator import generate_question
from video_creator import create_video
from youtube_uploader import upload_video

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
UPLOAD_INTERVAL_HOURS = 4   # Upload every 4 hours = 6 videos/day
VIDEOS_DIR = "videos"
COUNTER_FILE = "video_counter.json"

os.makedirs(VIDEOS_DIR, exist_ok=True)

def get_video_counter():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE) as f:
            return json.load(f).get("count", 1)
    return 1

def save_video_counter(count):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"count": count}, f)

def run_pipeline():
    """Full pipeline: Generate → Create Video → Upload → Cleanup."""
    video_num = get_video_counter()
    log.info(f"🚀 Starting pipeline for video #{video_num}")

    # Step 1: Generate question
    try:
        log.info("🧠 Generating GK question...")
        question_data = generate_question()
        log.info(f"✅ Question: {question_data['question']}")
    except Exception as e:
        log.error(f"❌ Question generation failed: {e}")
        return

    # Step 2: Create video
    video_path = os.path.join(VIDEOS_DIR, f"gk_quiz_{video_num}.mp4")
    try:
        log.info("🎬 Creating video...")
        create_video(question_data, video_path)
        log.info(f"✅ Video created: {video_path}")
    except Exception as e:
        log.error(f"❌ Video creation failed: {e}")
        return

    # Step 3: Upload to YouTube
    try:
        log.info("📤 Uploading to YouTube...")
        video_id = upload_video(video_path, question_data, video_num)
        log.info(f"✅ Uploaded: https://youtu.be/{video_id}")
    except Exception as e:
        log.error(f"❌ Upload failed: {e}")
        return

    # Step 4: Cleanup
    try:
        os.remove(video_path)
        log.info("🗑️  Temp video deleted")
    except Exception:
        pass

    save_video_counter(video_num + 1)
    log.info(f"🎉 Pipeline complete! Next run in {UPLOAD_INTERVAL_HOURS} hours.\n")

def main():
    log.info("=" * 50)
    log.info("🤖 GK YouTube Bot Started!")
    log.info(f"📅 Upload schedule: Every {UPLOAD_INTERVAL_HOURS} hours")
    log.info("=" * 50)

    # Run immediately on start
    run_pipeline()

    # Schedule recurring uploads
    schedule.every(UPLOAD_INTERVAL_HOURS).hours.do(run_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()