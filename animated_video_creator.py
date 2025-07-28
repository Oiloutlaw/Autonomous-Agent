import os
import sys
import openai
import requests
import time
import subprocess
from dotenv import load_dotenv
import elevenlabs
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from utils.platform_utils import get_ffmpeg_command, normalize_path, ensure_directory

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_key = os.getenv("ELEVENLABS_API_KEY")
MODELSLAB_KEY = os.getenv("MODELSLAB_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
DB_PATH = normalize_path("video_logs.db")

output_dir = normalize_path("output")
ensure_directory(output_dir)

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


init_db()


def log_upload(filename):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO uploads (filename) VALUES (?)", (filename,))
    conn.commit()
    conn.close()


def notify_user(video_title):
    print(f"📧 Notification: Video '{video_title}' has been created and uploaded!")


def break_script_into_scenes(script_text):
    prompt = f"""Break this YouTube Shorts script into a shot-by-shot production plan.
For each shot, include:
- Narration: (1 sentence max)
- Visual: (brief description)
- Prompt: (image generation prompt)

Format each shot like this:
Shot X:
Narration: [text here]
Visual: [description here]  
Prompt: [image prompt here]

SCRIPT:
{script_text}"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700
    )
    return response.choices[0].message.content


def generate_video(prompt_text, idx):
    url = "https://modelslab.com/api/v6/video/text2video_ultra"
    headers = {
        "Authorization": f"Bearer {MODELSLAB_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "key": MODELSLAB_KEY,
        "prompt": prompt_text,
        "aspect_ratio": "16:9",
        "duration": 4,
        "motion": "medium",
        "quality": "medium",
        "webhook": None,
        "seed": None
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    video_url = data.get("video") or (data.get("output") and data["output"][0])
    if not video_url:
        raise ValueError("❌ No video URL found in ModelsLab response.")

    try:
        vid_data = requests.get(video_url).content
    except Exception as e:
        raise RuntimeError(f"❌ Failed to download generated video: {e}")

    vid_path = normalize_path(os.path.join(output_dir, f"scene_{idx:02d}.mp4"))
    with open(vid_path, "wb") as f:
        f.write(vid_data)
    return vid_path


def generate_voiceover(text, filename):
    audio = elevenlabs.generate(
        text=text,
        voice="Rachel",
        model="eleven_monolingual_v1",
        api_key=eleven_key
    )
    out_path = normalize_path(os.path.join(output_dir, filename))
    with open(out_path, "wb") as f:
        f.write(audio)
    return out_path


def create_video(scenes):
    inputs = []
    for i, scene in enumerate(scenes):
        prompt = scene['image_prompt']
        narration = scene['narration']
        print(f"🎬 Scene {i+1}: {narration}")

        video_path = generate_video(prompt, i)
        audio_path = generate_voiceover(narration, f"audio_{i:02d}.mp3")

        output_path = normalize_path(os.path.join(output_dir, f"clip_{i:02d}.mp4"))
        try:
            ffmpeg_cmd = get_ffmpeg_command()
        except RuntimeError as e:
            print(f"❌ {e}")
            raise
            
        cmd = [
            ffmpeg_cmd, "-y",
            "-i", normalize_path(video_path),
            "-i", normalize_path(audio_path),
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest", "-pix_fmt", "yuv420p",
            output_path
        ]
        subprocess.run(cmd, check=True)
        inputs.append(output_path)

    concat_file = normalize_path(os.path.join(output_dir, "segments.txt"))
    with open(concat_file, "w") as f:
        for clip in inputs:
            abs_path = os.path.abspath(clip).replace('\\', '/')
            f.write(f"file '{abs_path}'\n")

    final_video = normalize_path(os.path.join(output_dir, "final_video.mp4"))
    try:
        ffmpeg_cmd = get_ffmpeg_command()
    except RuntimeError as e:
        print(f"❌ {e}")
        raise
        
    cmd = [ffmpeg_cmd, "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", final_video]
    subprocess.run(cmd, check=True)
    print(f"🎉 Final video created: {final_video}")
    return final_video


def upload_to_youtube(video_path, title="Motivational Shorts", description="Created by AI", category_id="22"):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request_body = {
        "snippet": {
            "categoryId": category_id,
            "title": title,
            "description": description,
            "tags": ["AI", "Motivation", "Shorts"]
        },
        "status": {"privacyStatus": "public"}
    }
    media_file = MediaFileUpload(video_path)
    response = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    ).execute()

    print("✅ Uploaded to YouTube:", response["id"])
    log_upload(video_path)
    notify_user(title)


def run_video_creator():
    sample_script = """[Scene 1: Alarm clock rings]
VO: Each day, greatness GETS UP before sunrise.
[Scene 2: Entrepreneurs making coffee]
VO: Morning rituals? They're not just habits. They're the COMMANDS we give ourselves.
[Scene 3: Meditation and exercise]
VO: Still your mind. See your success before it's real.
[Scene 4: Sunrise]
VO: This day is YOURS. What's your ritual?"""

    production_plan = break_script_into_scenes(sample_script)

    scenes = []
    current_scene = {}
    for line in production_plan.split("\n"):
        line = line.strip()
        if line.startswith("Narration:"):
            current_scene['narration'] = line.replace("Narration:", "").strip()
        elif line.startswith("Prompt:"):
            current_scene['image_prompt'] = line.replace("Prompt:", "").strip()
            if 'narration' in current_scene and 'image_prompt' in current_scene:
                scenes.append(current_scene.copy())
                current_scene = {}

    final_path = create_video(scenes)
    upload_to_youtube(final_path)


scheduler = BackgroundScheduler()
scheduler.add_job(run_video_creator, 'interval', minutes=15)
scheduler.start()


@app.route("/trigger-video", methods=["POST"])
def trigger_video():
    run_video_creator()
    return "Video triggered manually."


if __name__ == "__main__":
    print("🚀 Animated video agent running with scheduler and API endpoint...")
    app.run(host="0.0.0.0", port=8001)
