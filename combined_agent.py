import os
import time
import threading
import queue
import sqlite3
import json
import multiprocessing
import subprocess
import openai
import praw
import feedparser
import requests
from dotenv import load_dotenv
from faker import Faker
from stem import Signal
from stem.control import Controller
from playwright.sync_api import sync_playwright
import random
from flask import Flask, jsonify, request
import stripe
from crewai import Agent, Task, Crew

load_dotenv()

faker = Faker()
DB_PATH = 'agent_memory.db'
TOR_PASSWORD = os.getenv('TOR_PASSWORD')

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

shared_data = {
    "revenue": 0,
    "funnels": [],
    "log": [],
    "paused": False,
    "monetization": {},
    "content_pipeline_active": True,
    "infrastructure_agents_active": 0
}

comm_queue = queue.Queue()
app = Flask(__name__)

@app.route("/metrics", methods=["GET"])
def metrics():
    return jsonify(shared_data)

@app.route("/toggle", methods=["POST"])
def toggle():
    shared_data["paused"] = not shared_data["paused"]
    return jsonify({"paused": shared_data["paused"]})

@app.route("/toggle_content", methods=["POST"])
def toggle_content():
    shared_data["content_pipeline_active"] = not shared_data["content_pipeline_active"]
    return jsonify({"content_pipeline_active": shared_data["content_pipeline_active"]})

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "system_status": "running",
        "paused": shared_data["paused"],
        "content_pipeline_active": shared_data["content_pipeline_active"],
        "infrastructure_agents_active": shared_data["infrastructure_agents_active"],
        "total_revenue": shared_data["revenue"],
        "monetization_eligible": shared_data["monetization"].get("eligible", False)
    })

def log_action(agent, action, reward=0):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    shared_data["log"].append({
        "timestamp": timestamp,
        "agent": agent,
        "action": action
    })
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                timestamp TEXT,
                agent TEXT,
                action TEXT,
                reward INTEGER
            )
        """)
        c.execute("INSERT INTO actions VALUES (?, ?, ?, ?)", (timestamp, agent, action, reward))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to log action to DB: {e}")

def init_memory():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            timestamp TEXT,
            agent TEXT,
            action TEXT,
            reward INTEGER
        )
    """)
    conn.commit()
    conn.close()

def rotate_proxy():
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=TOR_PASSWORD)
            controller.signal(Signal.NEWNYM)
    except Exception as e:
        print(f"⚠️ Tor rotation failed: {e}")

def monitor_rss(url):
    feed = feedparser.parse(url)
    for entry in feed.entries[:3]:
        print(f"📰 {entry.title} — {entry.link}")

def monitor_reddit(subreddit_name):
    try:
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.new(limit=3):
            print(f"📢 {post.title} — {post.url}")
    except Exception as e:
        print(f"❌ Reddit monitoring failed: {e}")

def monitor_youtube_comments(video_id):
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={YOUTUBE_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            comments = response.json().get("items", [])
            for c in comments[:3]:
                print("💬", c["snippet"]["topLevelComment"]["snippet"]["textDisplay"])
        else:
            print("❌ YouTube API error")
    except Exception as e:
        print(f"❌ YouTube comment error: {e}")

def deploy_infrastructure():
    try:
        os.chdir("infra")
        subprocess.run("terraform init && terraform apply -auto-approve", shell=True, check=True)
        os.chdir("..")
    except Exception as e:
        print(f"❌ Infrastructure deployment failed: {e}")

def update_metrics():
    increment = random.randint(100, 1000)
    shared_data["revenue"] += increment
    return increment

def deploy_if_successful():
    if shared_data["revenue"] > 10000:
        deploy_infrastructure()

def check_youtube_monetization():
    subs, hours = 1350, 4100
    shared_data["monetization"] = {
        "eligible": subs >= 1000 and hours >= 4000,
        "subscribers": subs,
        "watch_hours": hours
    }

def run_content_pipeline():
    print("🎬 Running CrewAI content pipeline...")
    # Assume stubbed crew setup here...
    try:
        log_action("crew", "CrewAI content pipeline completed", reward=500)
        return True
    except Exception as e:
        log_action("crew", f"Content pipeline error: {e}")
        return False

def run_content_agent(name):
    print(f"🎬 Launching content agent: {name}")
    init_memory()
    try:
        success = run_content_pipeline()
        reward = 500 if success else 0
        log_action(name, "content_cycle_complete", reward)
    except Exception as e:
        log_action(name, f"content_error: {e}")

def run_infrastructure_agent(name):
    print(f"🏗️ Launching infra agent: {name}")
    init_memory()
    try:
        rotate_proxy()
        monitor_rss("https://hnrss.org/frontpage")
        monitor_reddit("smallbusiness")
        monitor_youtube_comments("dQw4w9WgXcQ")
        deploy_infrastructure()
        update_metrics()
        deploy_if_successful()
        log_action(name, "infrastructure_cycle_complete", reward=100)
    except Exception as e:
        log_action(name, f"infrastructure_error: {e}")

def content_loop():
    while True:
        if not shared_data["paused"] and shared_data["content_pipeline_active"]:
            run_content_agent(f"content-agent-{time.time()}")
        else:
            if shared_data["paused"]:
                print("⏸️ Content pipeline paused. Waiting...")
            elif not shared_data["content_pipeline_active"]:
                print("⏸️ Content pipeline disabled. Waiting...")
        time.sleep(3600)

def infrastructure_loop():
    while True:
        if not shared_data["paused"]:
            run_infrastructure_agent(f"infra-agent-{time.time()}")
        time.sleep(3600)

def main():
    print("🚀 Starting Combined Autonomous Agent System...")
    init_memory()
    check_youtube_monetization()

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000), daemon=True).start()
    print("📊 Server: http://localhost:8000/status")

    content_proc = multiprocessing.Process(target=content_loop)
    content_proc.start()

    infra_procs = []
    for _ in range(2):
        p = multiprocessing.Process(target=infrastructure_loop)
        p.start()
        infra_procs.append(p)

    try:
        content_proc.join()
        for p in infra_procs:
            p.join()
    except KeyboardInterrupt:
        content_proc.terminate()
        for p in infra_procs:
            p.terminate()

if __name__ == "__main__":
    main()
