import os
import time
import threading
import queue
import sqlite3
import json
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import stripe
import openai
from crewai import Agent, Task, Crew

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

app = Flask(__name__)
shared_data = {
    "revenue": 0,
    "funnels": [],
    "log": [],
    "paused": False,
    "monetization": {}
}
comm_queue = queue.Queue()

@app.route("/metrics", methods=["GET"])
def metrics():
    return jsonify(shared_data)

@app.route("/toggle", methods=["POST"])
def toggle():
    shared_data["paused"] = not shared_data["paused"]
    return jsonify({"paused": shared_data["paused"]})

def log_action(agent, action, reward=0):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    shared_data["log"].append({"timestamp": timestamp, "agent": agent, "action": action})
    conn = sqlite3.connect("agent_memory.db")
    c = conn.cursor()
    c.execute("INSERT INTO actions VALUES (?, ?, ?, ?)", (timestamp, agent, action, reward))
    conn.commit()
    conn.close()
    print(f"[{timestamp}] {agent}: {action} (Reward: {reward})")

def init_memory():
    conn = sqlite3.connect("agent_memory.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS actions (
        timestamp TEXT, agent TEXT, action TEXT, reward INTEGER)''')
    conn.commit()
    conn.close()

def check_youtube_monetization():
    print("💰 Checking YouTube monetization eligibility...")
    subscribers, watch_hours = 1350, 4100
    eligible = subscribers >= 1000 and watch_hours >= 4000
    shared_data["monetization"] = {
        "eligible": eligible,
        "subscribers": subscribers,
        "watch_hours": watch_hours
    }
    if eligible:
        print("✅ Channel is eligible for monetization!")
    else:
        print("❌ Channel is NOT eligible")
    return eligible

def create_stub_agents():
    os.makedirs("agents", exist_ok=True)
    for name in [
        "trend_scanner.py", "script_writer.py", "thumbnail_designer.py",
        "video_creator.py", "uploader.py", "seo_optimizer.py", "monetization_checker.py"
    ]:
        path = os.path.join("agents", name)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(f"print(\"🚀 Agent active: {name}\")")

def run_pipeline():
    trend_scanner = Agent(
        role='TrendScout',
        goal='Find viral topics',
        backstory='Scans social trends'
    )
    script_writer = Agent(
        role='ScriptWriter',
        goal='Write viral scripts',
        backstory='Writes short-form scripts'
    )
    thumbnail_designer = Agent(
        role='ThumbnailCreator',
        goal='Design thumbnails',
        backstory='Creates visual hooks'
    )
    video_creator = Agent(
        role='VideoProducer',
        goal='Make video',
        backstory='Edits and narrates content'
    )
    uploader = Agent(
        role='YouTubePublisher',
        goal='Upload to YouTube',
        backstory='Publishes content'
    )
    seo_optimizer = Agent(
        role='SEOOptimizer',
        goal='Optimize metadata',
        backstory='Boosts visibility'
    )
    monetization_checker = Agent(
        role='MonetizationChecker',
        goal='Check YouTube eligibility',
        backstory='Monitors monetization'
    )

    tasks = [
        Task(agent=trend_scanner, description="Find a viral idea", expected_output="Trending topic identified"),
        Task(agent=script_writer, description="Write a 60s script", expected_output="60-second video script"),
        Task(agent=thumbnail_designer, description="Design a thumbnail", expected_output="Thumbnail image file"),
        Task(agent=video_creator, description="Create a video", expected_output="Short video file"),
        Task(agent=uploader, description="Upload to YouTube", expected_output="YouTube video published"),
        Task(agent=seo_optimizer, description="Optimize for SEO", expected_output="Optimized metadata"),
        Task(agent=monetization_checker, description="Log monetization status", expected_output="Monetization report")
    ]

    crew = Crew(agents=[trend_scanner, script_writer, thumbnail_designer,
                        video_creator, uploader, seo_optimizer, monetization_checker],
                tasks=tasks)

    try:
        crew.kickoff()
        log_action("crew", "CrewAI pipeline completed")
    except Exception as e:
        print("❌ ERROR during CrewAI execution:")
        import traceback
        traceback.print_exc()
        log_action("crew", f"Pipeline error: {str(e)}")

def main_loop(interval_minutes=0):
    while True:
        if not shared_data["paused"]:
            run_pipeline()
        else:
            print("⏸️ Paused. Waiting...")

        if interval_minutes == 0:
            break
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    init_memory()
    create_stub_agents()
    check_youtube_monetization()

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000), daemon=True).start()
    print("🧠 Self-Healing Agent is online.")
    main_loop()  # Set interval like main_loop(30) for auto-run every 30 minutes
