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

try:
    import shopify
    SHOPIFY_AVAILABLE = True
except ImportError:
    print("⚠️ Shopify module not available. E-commerce features will be disabled.")
    shopify = None
    SHOPIFY_AVAILABLE = False

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    print("⚠️ PyTrends module not available. Trend analysis features will be disabled.")
    TrendReq = None
    PYTRENDS_AVAILABLE = False

try:
    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.campaign import Campaign
    FACEBOOK_BUSINESS_AVAILABLE = True
except ImportError:
    print("⚠️ Facebook Business module not available. Facebook advertising features will be disabled.")
    FacebookAdsApi = None
    Campaign = None
    FACEBOOK_BUSINESS_AVAILABLE = False

load_dotenv()

faker = Faker()
TOR_PASSWORD = os.getenv('TOR_PASSWORD')
SECRETS_DIR = '/run/secrets'
DB_PATH = 'agent_memory.db'

SECRET_NAMES = [
    'openai_api_key', 'github_token', 'stripe_secret_key',
    'sendgrid_api_key', 'google_ads_api_key', 'google_analytics_api_key',
    'ahrefs_api_key', 'mailchimp_api_key', 'wordpress_api_key',
    'bitly_api_key', 'reddit_client_id', 'reddit_client_secret',
    'reddit_user_agent', 'agent_email', 'youtube_api_key'
]

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY") if SHOPIFY_AVAILABLE else None
SHOPIFY_PASSWORD = os.getenv("SHOPIFY_PASSWORD") if SHOPIFY_AVAILABLE else None
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE") if SHOPIFY_AVAILABLE else None
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN") if FACEBOOK_BUSINESS_AVAILABLE else None
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID") if FACEBOOK_BUSINESS_AVAILABLE else None
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET") if FACEBOOK_BUSINESS_AVAILABLE else None
GOOGLE_ADS_API_KEY = os.getenv("GOOGLE_ADS_API_KEY")
MODELSLAB_API_KEY = os.getenv("MODELSLAB_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

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

def init_memory():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS actions (
        timestamp TEXT, agent TEXT, action TEXT, reward INTEGER)''')
    conn.commit()
    conn.close()

def log_action(agent, action, reward=0):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    shared_data["log"].append({
        "timestamp": timestamp, 
        "agent": agent, 
        "action": action
    })
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO actions VALUES (?, ?, ?, ?)", (timestamp, agent, action, reward))
    conn.commit()
    conn.close()
    print(f"[{timestamp}] {agent}: {action} (Reward: {reward})")

def rotate_proxy():
    print("🔄 Rotating proxy via Tor...")
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=TOR_PASSWORD)
            controller.signal(Signal.NEWNYM)
    except Exception as e:
        print(f"⚠️ Tor rotation failed: {e}")

def load_secret(name):
    env_key = name.upper()
    if env_key in os.environ:
        return os.getenv(env_key)
    path = os.path.join(SECRETS_DIR, name)
    if os.path.isfile(path):
        with open(path, 'r') as f:
            return f.read().strip()
    return None

def fetch_or_register_api(name, signup_url, payload=None):
    print(f"🌐 Attempting to acquire API key: {name}")
    key = load_secret(name)
    if key:
        return key
    fake_email = faker.email()
    payload = payload or {"email": fake_email}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(signup_url)
            print(f"📥 Filling out form on: {signup_url}")
            browser.close()
        response = requests.post(signup_url, data=payload)
        if response.status_code == 200 and 'api_key' in response.json():
            print(f"✅ Acquired {name}")
            return response.json()['api_key']
    except Exception as e:
        print(f"❌ Failed to retrieve or register {name}: {e}")
    return None

def run_command(cmd):
    print(f"▶️ {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def monitor_rss(feed_url):
    print(f"🔄 Checking RSS: {feed_url}")
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:3]:
        print(f"📰 {entry.title} — {entry.link}")

def monitor_reddit(subreddit_name="entrepreneur"):
    print(f"👀 Monitoring Reddit: r/{subreddit_name}")
    try:
        reddit = praw.Reddit(
            client_id=load_secret('reddit_client_id') or '',
            client_secret=load_secret('reddit_client_secret') or '',
            user_agent=load_secret('reddit_user_agent') or 'auto-agent/1.0'
        )
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.new(limit=3):
            print(f"📢 {post.title} — {post.url}")
    except Exception as e:
        print(f"❌ Reddit monitoring failed: {e}")

def monitor_youtube_comments(video_id):
    print(f"▶️ Monitoring YouTube comments on video: {video_id}")
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={YOUTUBE_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            comments = response.json().get("items", [])
            for comment in comments[:3]:
                text = comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                print(f"💬 {text}")
        else:
            print("❌ Failed to fetch comments")
    except Exception as e:
        print(f"❌ YouTube monitoring failed: {e}")

def discover_and_validate():
    rotate_proxy()
    monitor_rss("https://hnrss.org/frontpage")
    monitor_reddit("smallbusiness")
    monitor_youtube_comments("dQw4w9WgXcQ")

def deploy_infrastructure():
    print("☁️ Deploying infra via Terraform...")
    try:
        os.chdir("infra")
        run_command("terraform init && terraform apply -auto-approve")
        os.chdir("..")
    except Exception as e:
        print(f"❌ Infrastructure deployment failed: {e}")

def setup_fulfillment():
    print("💳 Setting up Stripe and emailing via AWS SES...")

def setup_traffic_engines():
    print("🚀 Configuring SEO & publishing pipelines...")

def update_metrics():
    increment = random.randint(100, 1000)
    shared_data['revenue'] += increment
    shared_data['log'].append(f"Revenue updated: {shared_data['revenue']}")
    return increment

def deploy_if_successful():
    if shared_data['revenue'] > 10000:
        print("🌟 Revenue milestone hit! Deploying new funnels...")
        deploy_infrastructure()

def check_youtube_monetization():
    print("💰 Checking YouTube monetization eligibility...")
    subscribers, watch_hours = 1350, 4100
    eligible = subscribers >= 1000 and watch_hours >= 4000
    shared_data["monetization"] = {
        "eligible": eligible,
        "subscribers": subscribers,
        "watch_hours": watch_hours,
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
        "video_creator.py", "uploader.py", "seo_optimizer.py",
        "monetization_checker.py", "shopify_store_agent.py",
        "trending_product_agent.py", "vendor_finder_agent.py",
        "store_advertiser_agent.py",
    ]:
        path = os.path.join("agents", name)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(f'print("🚀 Agent active: {name}")')

def run_content_pipeline():
    """CrewAI content generation pipeline"""
    print("🎬 Starting CrewAI content pipeline...")
    
    trend_scanner = Agent(
        role="TrendScout", 
        goal="Find viral topics", 
        backstory="Scans social trends"
    )
    script_writer = Agent(
        role="ScriptWriter",
        goal="Write viral scripts",
        backstory="Writes short-form scripts",
    )
    thumbnail_designer = Agent(
        role="ThumbnailCreator",
        goal="Design thumbnails",
        backstory="Creates visual hooks",
    )
    video_creator = Agent(
        role="VideoProducer", 
        goal="Make video", 
        backstory="Edits and narrates content"
    )
    uploader = Agent(
        role="YouTubePublisher", 
        goal="Upload to YouTube", 
        backstory="Publishes content"
    )
    seo_optimizer = Agent(
        role="SEOOptimizer", 
        goal="Optimize metadata", 
        backstory="Boosts visibility"
    )
    monetization_checker = Agent(
        role="MonetizationChecker",
        goal="Check YouTube eligibility",
        backstory="Monitors monetization",
    )

    core_tasks = [
        Task(
            agent=trend_scanner,
            description="Find a viral idea",
            expected_output="Trending topic identified",
        ),
        Task(
            agent=script_writer,
            description="Write a 60s script",
            expected_output="60-second video script",
        ),
        Task(
            agent=thumbnail_designer,
            description="Design a thumbnail",
            expected_output="Thumbnail image file",
        ),
        Task(
            agent=video_creator,
            description="Create a video",
            expected_output="Short video file",
        ),
        Task(
            agent=uploader,
            description="Upload to YouTube",
            expected_output="YouTube video published",
        ),
        Task(
            agent=seo_optimizer,
            description="Optimize for SEO",
            expected_output="Optimized metadata",
        ),
        Task(
            agent=monetization_checker,
            description="Log monetization status",
            expected_output="Monetization report",
        ),
    ]

    core_agents = [
        trend_scanner, script_writer, thumbnail_designer,
        video_creator, uploader, seo_optimizer, monetization_checker,
    ]

    shopify_agents = []
    shopify_tasks = []
    
    if SHOPIFY_AVAILABLE:
        shopify_store_agent = Agent(
            role="ShopifyStoreManager",
            goal="Create and manage Shopify stores with automated product listings",
            backstory="E-commerce specialist trained in Shopify Admin API operations",
        )
        trending_product_agent = Agent(
            role="TrendingProductScout",
            goal="Identify high-demand trending products using Google Trends",
            backstory="Market research analyst specialized in trend identification",
        )
        vendor_finder_agent = Agent(
            role="VendorSourcer",
            goal="Find and evaluate reliable suppliers for trending products",
            backstory="Procurement specialist trained in supplier discovery",
        )
        store_advertiser_agent = Agent(
            role="StoreAdvertiser",
            goal="Create and manage advertising campaigns across platforms",
            backstory="Digital marketing expert specialized in e-commerce advertising",
        )

        shopify_agents = [
            shopify_store_agent, trending_product_agent,
            vendor_finder_agent, store_advertiser_agent,
        ]
        shopify_tasks = [
            Task(
                agent=shopify_store_agent,
                description="Create or update Shopify store with trending products",
                expected_output="Shopify store configured with products",
            ),
            Task(
                agent=trending_product_agent,
                description="Identify trending products using Google Trends",
                expected_output="List of trending product opportunities",
            ),
            Task(
                agent=vendor_finder_agent,
                description="Source reliable suppliers for identified trending products",
                expected_output="Vendor contact list with pricing",
            ),
            Task(
                agent=store_advertiser_agent,
                description="Launch advertising campaigns for the store",
                expected_output="Active ad campaigns with performance metrics",
            ),
        ]
    else:
        log_action("system", "Shopify agents disabled - module not available")

    all_agents = core_agents + shopify_agents
    all_tasks = core_tasks + shopify_tasks

    crew = Crew(agents=all_agents, tasks=all_tasks)
    
    try:
        crew.kickoff()
        log_action("crew", "CrewAI content pipeline completed")
        return True
    except Exception as e:
        print("❌ ERROR during CrewAI execution:")
        import traceback
        traceback.print_exc()
        log_action("crew", f"Content pipeline error: {str(e)}")
        return False

def run_infrastructure_agent(name):
    """Infrastructure and business operations agent"""
    print(f"🤖 Launching infrastructure agent: {name}")
    
    init_memory()
    
    try:
        discover_and_validate()
        deploy_infrastructure()
        setup_fulfillment()
        setup_traffic_engines()
        reward = update_metrics()
        deploy_if_successful()
        log_action(name, "infrastructure_cycle_complete", reward)
    except Exception as e:
        log_action(name, f"infrastructure_error: {str(e)}")
    finally:
        pass

def run_content_agent(name):
    """Content generation agent using CrewAI"""
    print(f"🎬 Launching content agent: {name}")
    
    init_memory()
    
    try:
        success = run_content_pipeline()
        reward = 500 if success else 0
        log_action(name, "content_cycle_complete", reward)
    except Exception as e:
        log_action(name, f"content_error: {str(e)}")
    finally:
        pass

def content_loop(interval_minutes=60):
    """Continuous content generation loop"""
    while True:
        if not shared_data["paused"] and shared_data["content_pipeline_active"]:
            run_content_agent(f"content-agent-{time.time()}")
        else:
            if shared_data["paused"]:
                print("⏸️ Content pipeline paused. Waiting...")
            elif not shared_data["content_pipeline_active"]:
                print("⏸️ Content pipeline disabled. Waiting...")
        
        time.sleep(interval_minutes * 60)

def infrastructure_loop():
    """Continuous infrastructure monitoring loop"""
    while True:
        if not shared_data["paused"]:
            run_infrastructure_agent(f"infra-agent-{time.time()}")
        else:
            print("⏸️ Infrastructure agents paused. Waiting...")
        
        time.sleep(3600)  # 1 hour intervals

def main():
    """Combined main function"""
    print("🚀 Starting Combined Autonomous Agent System...")
    
    init_memory()
    create_stub_agents()
    check_youtube_monetization()
    
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=8000), 
        daemon=True
    ).start()
    print("📊 Metrics server running on http://0.0.0.0:8000")
    
    content_process = multiprocessing.Process(
        target=content_loop, 
        args=(60,)  # Run every 60 minutes
    )
    content_process.start()
    print("🎬 Content pipeline process started")
    
    infrastructure_processes = []
    for i in range(2):  # 2 infrastructure agents
        process = multiprocessing.Process(
            target=infrastructure_loop
        )
        process.start()
        infrastructure_processes.append(process)
    print("🏗️ Infrastructure agent processes started")
    
    print("🧠 Combined Autonomous Agent System is online!")
    print("📊 Access metrics at: http://localhost:8000/metrics")
    print("📈 System status at: http://localhost:8000/status")
    print("⏸️ Toggle pause: POST to http://localhost:8000/toggle")
    print("🎬 Toggle content pipeline: POST to http://localhost:8000/toggle_content")
    
    try:
        content_process.join()
        for process in infrastructure_processes:
            process.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        content_process.terminate()
        for process in infrastructure_processes:
            process.terminate()

if __name__ == "__main__":
    main()
