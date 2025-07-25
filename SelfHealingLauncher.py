import os
import time
import subprocess
import threading
import queue
import sqlite3
import json

from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
import openai
import praw
import feedparser
import requests
from faker import Faker
from stem import Signal
from stem.control import Controller
from playwright.sync_api import sync_playwright
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# CrewAI imports
from crewai import Agent, Task, Crew

# Load environment variables
load_dotenv()
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Faker for generating fake identities
faker = Faker()

# Tor config
TOR_PASSWORD = os.getenv('TOR_PASSWORD')

# Paths & DB setup
PROJECT_DIR = os.path.dirname(__file__)
SECRETS_DIR = '/run/secrets'
DB_PATH = os.path.join(PROJECT_DIR, 'agent_memory.db')
SECRET_NAMES = [
    'openai_api_key',
    'github_token',
    'stripe_secret_key',
    'sendgrid_api_key',
    'google_ads_api_key',
    'google_analytics_api_key',
    'ahrefs_api_key',
    'mailchimp_api_key',
    'wordpress_api_key',
    'bitly_api_key',
    'reddit_client_id',
    'reddit_client_secret',
    'reddit_user_agent',
    'agent_email',
    'youtube_api_key',
]

# Shared data for metrics and control
shared_data = {"revenue": 0, "funnels": [], "log": [], "paused": False}
comm_queue = queue.Queue()

# Flask app for metrics
app = Flask(__name__)


@app.route("/metrics")
def metrics():
    return jsonify(shared_data)


@app.route("/toggle", methods=["POST"])
def toggle():
    shared_data["paused"] = not shared_data["paused"]
    return jsonify({"paused": shared_data["paused"]})


# Initialize memory DB
def init_memory():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS actions (
           timestamp TEXT, agent TEXT, action TEXT, reward INTEGER)'''
    )
    conn.commit()
    conn.close()


init_memory()

# API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Validate API key
if not openai.api_key or openai.api_key.startswith("your-"):
    print(
        "❌ ERROR: Invalid or missing OpenAI API key. Please set the OPENAI_API_KEY environment variable to a valid key."
    )
    import sys

    sys.exit(1)


# YouTube monetization check function
def check_youtube_monetization():
    print("💰 Checking YouTube monetization eligibility...")
    # Replace these values with live API fetch if desired
    subscribers = 1350
    watch_hours = 4100
    eligible = subscribers >= 1000 and watch_hours >= 4000
    if eligible:
        print("✅ Channel is eligible for monetization!")
    else:
        print("❌ Channel is NOT eligible. Needs 1000 subs & 4000 watch hours.")
    return {"eligible": eligible, "subscribers": subscribers, "watch_hours": watch_hours}


# Upload video to YouTube
def upload_to_youtube(video_file, title, description):
    if not YOUTUBE_API_KEY:
        print("⚠️ YouTube upload skipped (missing API key)")
        return
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request_body = {
        'snippet': {
            'categoryId': '22',
            'title': title,
            'description': description,
            'tags': ['money', 'hustle', 'finance'],
        },
        'status': {'privacyStatus': 'public'},
    }
    media = MediaFileUpload(video_file, resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=request_body, media_body=media)
    response = request.execute()
    print(f"✅ Uploaded to YouTube: {response.get('id')}")


# Define CrewAI agents
trend_scanner = Agent(
    role='TrendScout',
    goal='Identify high-potential YouTube topics from Reddit/TikTok/Google Trends',
    backstory='A social media analyst trained to scan Reddit, TikTok, and Google Trends to find the most viral video topics.',
)

script_writer = Agent(
    role='ScriptWriter',
    goal='Write a 60-second viral video script for the chosen topic',
    backstory='A creative storyteller who crafts punchy, engaging short scripts for social content based on trending topics.',
)

thumbnail_designer = Agent(
    role='ThumbnailCreator',
    goal='Generate a high-CTR thumbnail using AI tools and trends',
    backstory='A digital designer trained in pattern recognition and audience psychology to maximize YouTube click-through rates.',
)

video_creator = Agent(
    role='VideoProducer',
    goal='Convert scripts into short video files with dynamic visuals and narration',
    backstory='An AI-powered video producer that transforms scripts and visuals into polished, high-conversion short videos.',
)

uploader = Agent(
    role='YouTubePublisher',
    goal='Upload the final video with proper title, description, and tags',
    backstory='An automation expert responsible for publishing content with precise metadata on YouTube to maximize visibility.',
)

seo_optimizer = Agent(
    role='SEOOptimizer',
    goal='Optimize video metadata, tags, and social posts to boost traffic and visibility',
    backstory='An SEO strategist trained in YouTube’s ranking algorithm to amplify reach through data-driven optimizations.',
)

monetization_checker = Agent(
    role='MonetizationChecker',
    goal='Evaluate if the YouTube channel meets monetization criteria and report stats',
    backstory='A policy compliance agent that monitors and reports monetization eligibility across YouTube metrics.',
)

# Define tasks and crew
tasks = [
    Task(
        agent=trend_scanner,
        description="Find a viral video idea",
        expected_output="Trending topic identified",
    ),
    Task(
        agent=script_writer,
        description="Write a short script about the idea",
        expected_output="60-second video script",
    ),
    Task(
        agent=thumbnail_designer,
        description="Design a thumbnail based on script",
        expected_output="Thumbnail image file",
    ),
    Task(
        agent=video_creator,
        description="Generate a video from script and thumbnail",
        expected_output="Short video file",
    ),
    Task(
        agent=uploader,
        description="Upload video and write basic title/description",
        expected_output="YouTube video published",
    ),
    Task(
        agent=seo_optimizer,
        description="Enhance metadata and traffic routing for YouTube SEO",
        expected_output="Optimized metadata",
    ),
    Task(
        agent=monetization_checker,
        description="Run monetization check and log eligibility",
        expected_output="Monetization report",
    ),
]

crew = Crew(
    agents=[
        trend_scanner,
        script_writer,
        thumbnail_designer,
        video_creator,
        uploader,
        seo_optimizer,
        monetization_checker,
    ],
    tasks=tasks,
)

# Main entrypoint
if __name__ == "__main__":
    # Start metrics server
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000), daemon=True).start()
    time.sleep(2)

    # Initial monetization check
    shared_data["monetization"] = check_youtube_monetization()

    # Ensure agent stubs exist in /agents
    AGENT_DIR = os.path.join(PROJECT_DIR, "agents")
    os.makedirs(AGENT_DIR, exist_ok=True)
    for fname in [
        "trend_scanner.py",
        "script_writer.py",
        "thumbnail_designer.py",
        "video_creator.py",
        "uploader.py",
        "seo_optimizer.py",
        "monetization_checker.py",
    ]:
        path = os.path.join(AGENT_DIR, fname)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"print(\"🚀 Agent active: {fname}\")\n")

    # Launch CrewAI pipeline
try:
    crew.kickoff()
except Exception as e:
    # Catch authentication errors and other issues
    err_msg = str(e)
    print(f"❌ ERROR during CrewAI execution: {err_msg}")
    import sys

    sys.exit(1)
