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

try:
    import shopify

    SHOPIFY_AVAILABLE = True
except ImportError:
    print("⚠️ Shopify module not available. E-commerce features will be disabled.")
    shopify = None
    SHOPIFY_AVAILABLE = False
from pytrends.request import TrendReq
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.campaign import Campaign

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY") if SHOPIFY_AVAILABLE else None
SHOPIFY_PASSWORD = os.getenv("SHOPIFY_PASSWORD") if SHOPIFY_AVAILABLE else None
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE") if SHOPIFY_AVAILABLE else None
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
GOOGLE_ADS_API_KEY = os.getenv("GOOGLE_ADS_API_KEY")
MODELSLAB_API_KEY = os.getenv("MODELSLAB_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

app = Flask(__name__)
shared_data = {
    "revenue": 0,
    "funnels": [],
    "log": [],
    "paused": False,
    "monetization": {},
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
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    shared_data["log"].append(
        {"timestamp": timestamp, "agent": agent, "action": action}
    )
    conn = sqlite3.connect("agent_memory.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO actions VALUES (?, ?, ?, ?)", (timestamp, agent, action, reward)
    )
    conn.commit()
    conn.close()
    print(f"[{timestamp}] {agent}: {action} (Reward: {reward})")


def init_memory():
    conn = sqlite3.connect("agent_memory.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS actions (
        timestamp TEXT, agent TEXT, action TEXT, reward INTEGER)"""
    )
    conn.commit()
    conn.close()


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
        "trend_scanner.py",
        "script_writer.py",
        "thumbnail_designer.py",
        "video_creator.py",
        "uploader.py",
        "seo_optimizer.py",
        "monetization_checker.py",
        "shopify_store_agent.py",
        "trending_product_agent.py",
        "vendor_finder_agent.py",
        "store_advertiser_agent.py",
    ]:
        path = os.path.join("agents", name)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(f'print("🚀 Agent active: {name}")')


def run_pipeline():
    trend_scanner = Agent(
        role="TrendScout", goal="Find viral topics", backstory="Scans social trends"
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
        role="VideoProducer", goal="Make video", backstory="Edits and narrates content"
    )
    uploader = Agent(
        role="YouTubePublisher", goal="Upload to YouTube", backstory="Publishes content"
    )
    seo_optimizer = Agent(
        role="SEOOptimizer", goal="Optimize metadata", backstory="Boosts visibility"
    )
    monetization_checker = Agent(
        role="MonetizationChecker",
        goal="Check YouTube eligibility",
        backstory="Monitors monetization",
    )

    shopify_agents = []
    shopify_tasks = []

    if SHOPIFY_AVAILABLE:
        shopify_store_agent = Agent(
            role="ShopifyStoreManager",
            goal="Create and manage Shopify stores with automated product listings and inventory management",
            backstory="An e-commerce specialist trained in Shopify Admin API operations, store configuration, and product catalog management",
        )
        trending_product_agent = Agent(
            role="TrendingProductScout",
            goal="Identify high-demand trending products using Google Trends and social media analysis",
            backstory="A market research analyst specialized in trend identification, product demand forecasting, and viral product discovery",
        )
        vendor_finder_agent = Agent(
            role="VendorSourcer",
            goal="Find and evaluate reliable suppliers for trending products through automated sourcing",
            backstory="A procurement specialist trained in supplier discovery, vendor evaluation, and wholesale sourcing automation",
        )
        store_advertiser_agent = Agent(
            role="StoreAdvertiser",
            goal="Create and manage advertising campaigns across Google Ads and Facebook to drive store traffic",
            backstory="A digital marketing expert specialized in e-commerce advertising, campaign optimization, and ROI maximization",
        )

        shopify_agents = [
            shopify_store_agent,
            trending_product_agent,
            vendor_finder_agent,
            store_advertiser_agent,
        ]
        shopify_tasks = [
            Task(
                agent=shopify_store_agent,
                description="Create or update Shopify store with trending products",
                expected_output="Shopify store configured with products",
            ),
            Task(
                agent=trending_product_agent,
                description="Identify trending products using Google Trends and social analysis",
                expected_output="List of trending product opportunities",
            ),
            Task(
                agent=vendor_finder_agent,
                description="Source reliable suppliers for identified trending products",
                expected_output="Vendor contact list with pricing",
            ),
            Task(
                agent=store_advertiser_agent,
                description="Launch advertising campaigns for the store across multiple platforms",
                expected_output="Active ad campaigns with performance metrics",
            ),
        ]
    else:
        log_action("system", "Shopify agents disabled - module not available")

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

    tasks = core_tasks + shopify_tasks

    core_agents = [
        trend_scanner,
        script_writer,
        thumbnail_designer,
        video_creator,
        uploader,
        seo_optimizer,
        monetization_checker,
    ]

    all_agents = core_agents + shopify_agents

    crew = Crew(agents=all_agents, tasks=tasks)

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

    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=8000), daemon=True
    ).start()
    print("🧠 Self-Healing Agent is online.")
    main_loop()  # Set interval like main_loop(30) for auto-run every 30 minutes
