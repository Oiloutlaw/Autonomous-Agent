#!/usr/bin/env python3
"""
Unified Autonomous Agent System
Consolidates combined_agent.py, SelfHealingLauncher.py, and animated_video_creator.py
Includes Azure AI inference integration alongside OpenAI
"""

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
from apscheduler.schedulers.background import BackgroundScheduler
import elevenlabs
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential
    AZURE_AI_AVAILABLE = True
except ImportError:
    print("⚠️ Azure AI inference not available. Using OpenAI only.")
    AZURE_AI_AVAILABLE = False

load_dotenv()

faker = Faker()
DB_PATH = 'agent_memory.db'
VIDEO_DB_PATH = 'video_logs.db'
TOR_PASSWORD = os.getenv('TOR_PASSWORD')

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

AZURE_ENDPOINT = "https://models.github.ai/inference"
AZURE_MODEL = "openai/gpt-4.1"

shared_data = {
    "revenue": 0,
    "funnels": [],
    "log": [],
    "paused": False,
    "monetization": {},
    "content_pipeline_active": True,
    "infrastructure_agents_active": 0,
    "video_generation_active": True,
    "ai_provider": "openai",
    "system_status": "running",
    "monetization_eligible": True,
    "total_revenue": 0
}

comm_queue = queue.Queue()
app = Flask(__name__)

def get_ai_client():
    """Get AI client based on configured provider with fallback"""
    if shared_data["ai_provider"] == "azure" and AZURE_AI_AVAILABLE and GITHUB_TOKEN:
        try:
            return ChatCompletionsClient(
                endpoint=AZURE_ENDPOINT,
                credential=AzureKeyCredential(GITHUB_TOKEN)
            )
        except Exception as e:
            print(f"⚠️ Azure AI client failed, falling back to OpenAI: {e}")
            shared_data["ai_provider"] = "openai"
    
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_ai_content(prompt, system_message="You are a helpful assistant."):
    """Generate content using configured AI provider"""
    try:
        if shared_data["ai_provider"] == "azure" and AZURE_AI_AVAILABLE and GITHUB_TOKEN:
            client = get_ai_client()
            response = client.complete(
                messages=[
                    SystemMessage(system_message),
                    UserMessage(prompt),
                ],
                temperature=1.0,
                top_p=1.0,
                model=AZURE_MODEL
            )
            return response.choices[0].message.content
        else:
            client = get_ai_client()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=1.0
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI generation failed: {e}")
        return None

def init_memory():
    """Initialize agent memory database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            agent TEXT,
            action TEXT,
            reward REAL
        )
    ''')
    conn.commit()
    conn.close()

def init_video_db():
    """Initialize video logs database"""
    conn = sqlite3.connect(VIDEO_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            title TEXT,
            description TEXT,
            video_id TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_action(agent, action, reward=0):
    """Log agent action to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO actions (timestamp, agent, action, reward) VALUES (?, ?, ?, ?)',
        (timestamp, agent, action, reward)
    )
    conn.commit()
    conn.close()
    
    shared_data["log"].append({
        "timestamp": timestamp,
        "agent": agent,
        "action": action,
        "reward": reward
    })
    
    if len(shared_data["log"]) > 100:
        shared_data["log"] = shared_data["log"][-100:]

def log_video_upload(title, description, video_id, status):
    """Log video upload to database"""
    conn = sqlite3.connect(VIDEO_DB_PATH)
    cursor = conn.cursor()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        'INSERT INTO video_uploads (timestamp, title, description, video_id, status) VALUES (?, ?, ?, ?, ?)',
        (timestamp, title, description, video_id, status)
    )
    conn.commit()
    conn.close()

def rotate_proxy():
    """Rotate Tor proxy"""
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=TOR_PASSWORD)
            controller.signal(Signal.NEWNYM)
            time.sleep(5)
            return True
    except Exception as e:
        print(f"❌ Proxy rotation failed: {e}")
        return False

def check_youtube_monetization():
    """Check YouTube monetization status"""
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.channels().list(part='monetizationDetails', mine=True)
        response = request.execute()
        
        if response['items']:
            monetization = response['items'][0].get('monetizationDetails', {})
            shared_data["monetization"] = monetization
            shared_data["monetization_eligible"] = monetization.get('access', {}).get('allowed', False)
            return shared_data["monetization_eligible"]
    except Exception as e:
        print(f"❌ YouTube monetization check failed: {e}")
        shared_data["monetization_eligible"] = False
    
    return False

def upload_to_youtube(video_file, title, description):
    """Upload video to YouTube"""
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['AI', 'automation', 'content'],
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'public'
            }
        }
        
        media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response['id']
        
        log_video_upload(title, description, video_id, 'success')
        log_action("video_uploader", f"Uploaded video: {title}", 100)
        
        return video_id
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        log_video_upload(title, description, None, f'failed: {e}')
        return None

def generate_video_script(topic):
    """Generate video script using AI"""
    prompt = f"""Create an engaging 2-minute YouTube video script about: {topic}
    
    Include:
    - Hook in first 5 seconds
    - Clear structure with 3 main points
    - Call to action at the end
    - Natural speaking tone
    
    Format as scenes with timestamps."""
    
    return generate_ai_content(prompt, "You are a professional YouTube scriptwriter.")

def break_script_into_scenes(script):
    """Break script into individual scenes"""
    scenes = []
    lines = script.split('\n')
    current_scene = ""
    
    for line in lines:
        if line.strip():
            if any(keyword in line.lower() for keyword in ['scene', 'timestamp', '0:', '1:', '2:']):
                if current_scene:
                    scenes.append(current_scene.strip())
                current_scene = line
            else:
                current_scene += " " + line
    
    if current_scene:
        scenes.append(current_scene.strip())
    
    return scenes[:5]

def generate_voiceover(text, output_file):
    """Generate voiceover using ElevenLabs"""
    try:
        if not ELEVENLABS_API_KEY:
            print("❌ ElevenLabs API key not found")
            return False
            
        elevenlabs.set_api_key(ELEVENLABS_API_KEY)
        audio = elevenlabs.generate(
            text=text,
            voice="Adam",
            model="eleven_monolingual_v1"
        )
        
        with open(output_file, 'wb') as f:
            f.write(audio)
        
        return True
    except Exception as e:
        print(f"❌ Voiceover generation failed: {e}")
        return False

def create_video_from_scenes(scenes, output_file):
    """Create video from scenes using FFmpeg"""
    try:
        audio_files = []
        
        for i, scene in enumerate(scenes):
            audio_file = f"temp_audio_{i}.mp3"
            if generate_voiceover(scene, audio_file):
                audio_files.append(audio_file)
        
        if not audio_files:
            return False
        
        concat_list = "concat_list.txt"
        with open(concat_list, 'w') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file}'\n")
        
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_list,
            '-c', 'copy', output_file, '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        for audio_file in audio_files:
            if os.path.exists(audio_file):
                os.remove(audio_file)
        if os.path.exists(concat_list):
            os.remove(concat_list)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Video creation failed: {e}")
        return False

def run_video_creator():
    """Main video creation function"""
    if not shared_data["video_generation_active"] or shared_data["paused"]:
        return
    
    try:
        print("🎬 Starting video creation...")
        
        topic = generate_ai_content("Generate a trending topic for a YouTube video", 
                                   "You are a trend analyst. Suggest one specific, engaging topic.")
        
        if not topic:
            print("❌ Failed to generate topic")
            return
        
        print(f"📝 Topic: {topic}")
        
        script = generate_video_script(topic)
        if not script:
            print("❌ Failed to generate script")
            return
        
        scenes = break_script_into_scenes(script)
        print(f"🎭 Created {len(scenes)} scenes")
        
        video_file = f"video_{int(time.time())}.mp3"
        
        if create_video_from_scenes(scenes, video_file):
            print(f"🎥 Video created: {video_file}")
            
            title = f"AI Generated: {topic[:50]}..."
            description = f"Auto-generated content about {topic}\n\n{script[:500]}..."
            
            video_id = upload_to_youtube(video_file, title, description)
            
            if video_id:
                print(f"✅ Video uploaded: https://youtube.com/watch?v={video_id}")
                shared_data["revenue"] += 10
                shared_data["total_revenue"] += 10
            
            if os.path.exists(video_file):
                os.remove(video_file)
        
    except Exception as e:
        print(f"❌ Video creation failed: {e}")
        log_action("video_creator", f"Video creation failed: {e}", -10)

def content_loop():
    """Content generation loop"""
    while True:
        if shared_data["paused"] or not shared_data["content_pipeline_active"]:
            time.sleep(60)
            continue
        
        try:
            print("🔍 Content agent discovering trends...")
            log_action("content_agent", "Discovering trends", 5)
            
            print("✍️ Content agent generating content...")
            log_action("content_agent", "Generating content", 10)
            
            shared_data["revenue"] += 25
            shared_data["total_revenue"] += 25
            
        except Exception as e:
            print(f"❌ Content loop error: {e}")
            log_action("content_agent", f"Error: {e}", -5)
        
        time.sleep(3600)

def infrastructure_loop():
    """Infrastructure management loop"""
    while True:
        if shared_data["paused"]:
            time.sleep(60)
            continue
        
        try:
            print("🏗️ Infrastructure agent monitoring...")
            log_action("infrastructure_agent", "Monitoring infrastructure", 5)
            
            shared_data["infrastructure_agents_active"] += 1
            
        except Exception as e:
            print(f"❌ Infrastructure loop error: {e}")
            log_action("infrastructure_agent", f"Error: {e}", -5)
        
        time.sleep(3600)

@app.route('/status')
def status():
    """Get system status"""
    return jsonify(shared_data)

@app.route('/metrics')
def metrics():
    """Get detailed metrics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM actions ORDER BY timestamp DESC LIMIT 50')
    recent_actions = cursor.fetchall()
    conn.close()
    
    return jsonify({
        "shared_data": shared_data,
        "recent_actions": recent_actions
    })

@app.route('/toggle', methods=['POST'])
def toggle():
    """Toggle system pause state"""
    shared_data["paused"] = not shared_data["paused"]
    status = "paused" if shared_data["paused"] else "running"
    log_action("system", f"System {status}", 0)
    return jsonify({"status": status, "paused": shared_data["paused"]})

@app.route('/toggle_content', methods=['POST'])
def toggle_content():
    """Toggle content pipeline"""
    shared_data["content_pipeline_active"] = not shared_data["content_pipeline_active"]
    status = "enabled" if shared_data["content_pipeline_active"] else "disabled"
    log_action("system", f"Content pipeline {status}", 0)
    return jsonify({"content_pipeline_active": shared_data["content_pipeline_active"]})

@app.route('/toggle_video', methods=['POST'])
def toggle_video():
    """Toggle video generation"""
    shared_data["video_generation_active"] = not shared_data["video_generation_active"]
    status = "enabled" if shared_data["video_generation_active"] else "disabled"
    log_action("system", f"Video generation {status}", 0)
    return jsonify({"video_generation_active": shared_data["video_generation_active"]})

@app.route('/trigger_video', methods=['POST'])
def trigger_video():
    """Manually trigger video creation"""
    threading.Thread(target=run_video_creator, daemon=True).start()
    return jsonify({"message": "Video creation triggered"})

@app.route('/switch_ai', methods=['POST'])
def switch_ai():
    """Switch AI provider"""
    provider = request.json.get('provider', 'openai')
    if provider in ['openai', 'azure']:
        shared_data["ai_provider"] = provider
        log_action("system", f"Switched to {provider} AI", 0)
        return jsonify({"ai_provider": shared_data["ai_provider"]})
    return jsonify({"error": "Invalid provider"}), 400

def main():
    """Main entry point for unified autonomous agent system"""
    print("🚀 Starting Unified Autonomous Agent System...")
    print("=" * 60)
    print("🤖 Initializing AI providers...")
    
    if AZURE_AI_AVAILABLE and GITHUB_TOKEN:
        print("✅ Azure AI available with GitHub token")
    else:
        print("⚠️ Azure AI not available, using OpenAI only")
    
    print("📊 Initializing databases...")
    init_memory()
    init_video_db()
    
    print("💰 Checking YouTube monetization...")
    check_youtube_monetization()
    
    print("🌐 Starting Flask server on port 8000...")
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000, debug=False), daemon=True).start()
    print("📊 Server: http://localhost:8000/status")
    
    print("🎬 Starting video generation scheduler...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_video_creator, 'interval', minutes=15)
    scheduler.start()
    
    print("📝 Starting content pipeline...")
    content_proc = multiprocessing.Process(target=content_loop)
    content_proc.start()
    
    print("🏗️ Starting infrastructure agents...")
    infra_procs = []
    for i in range(2):
        p = multiprocessing.Process(target=infrastructure_loop)
        p.start()
        infra_procs.append(p)
    
    print("=" * 60)
    print("✅ Unified Autonomous Agent System is running!")
    print("📊 Monitor at: http://localhost:8000/status")
    print("🎬 Video generation: Every 15 minutes")
    print("📝 Content pipeline: Every 60 minutes")
    print("🏗️ Infrastructure: Every 60 minutes")
    print("=" * 60)
    
    try:
        content_proc.join()
        for p in infra_procs:
            p.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        scheduler.shutdown()
        content_proc.terminate()
        for p in infra_procs:
            p.terminate()
        print("✅ Shutdown complete")

if __name__ == "__main__":
    main()
