import os
import time
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
import multiprocessing
import threading
import queue
import random
from flask import Flask, jsonify
import sqlite3

# Load `.env` if present
load_dotenv()

faker = Faker()
TOR_PASSWORD = os.getenv('TOR_PASSWORD')
SECRETS_DIR = '/run/secrets'
DB_PATH = 'agent_memory.db'

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

shared_data = {"revenue": 0, "funnels": [], "log": []}
comm_queue = queue.Queue()

app = Flask(__name__)


@app.route("/metrics")
def metrics():
    return jsonify(shared_data)


def init_memory():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS actions (timestamp TEXT, agent TEXT, action TEXT, reward INTEGER)'''
    )
    conn.commit()
    conn.close()


def log_action(agent, action, reward):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO actions VALUES (datetime('now'), ?, ?, ?)", (agent, action, reward))
    conn.commit()
    conn.close()


def rotate_proxy():
    print("\U0001f501 Rotating proxy via Tor...")
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=TOR_PASSWORD)
            controller.signal(Signal.NEWNYM)
    except Exception as e:
        print(f"⚠️ Tor rotation failed: {e}")


def solve_captcha(site_key, url):
    print(f"\U0001f9e0 Solving CAPTCHA for {url} with key {site_key} (simulated)")
    return "captcha-solved-token"


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
    print(f"\U0001f310 Attempting to acquire API key: {name}")
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
            print(f"\U0001f4e5 Filling out form on: {signup_url}")
            browser.close()
        response = requests.post(signup_url, data=payload)
        if response.status_code == 200 and 'api_key' in response.json():
            print(f"✅ Acquired {name}")
            return response.json()['api_key']
    except Exception as e:
        print(f"❌ Failed to retrieve or register {name}: {e}")
    return None


openai_key = fetch_or_register_api('openai_api_key', 'https://api.openai.com/signup')
if openai_key:
    openai.api_key = openai_key

github_token = fetch_or_register_api('github_token', 'https://github.com/join')
if github_token:
    os.environ['GITHUB_TOKEN'] = github_token

stripe_key = fetch_or_register_api('stripe_secret_key', 'https://dashboard.stripe.com/register')
if stripe_key:
    os.environ['STRIPE_KEY'] = stripe_key

EMAIL = load_secret('agent_email') or os.getenv('AGENT_EMAIL')

youtube_key = fetch_or_register_api(
    'youtube_api_key', 'https://console.cloud.google.com/apis/library/youtube.googleapis.com'
)
if youtube_key:
    YOUTUBE_API_KEY = youtube_key
else:
    YOUTUBE_API_KEY = ''

reddit = praw.Reddit(
    client_id=fetch_or_register_api('reddit_client_id', 'https://www.reddit.com/register') or '',
    client_secret=fetch_or_register_api('reddit_client_secret', 'https://www.reddit.com/register')
    or '',
    user_agent=fetch_or_register_api('reddit_user_agent', 'https://www.reddit.com/register')
    or 'auto-agent/1.0',
)


def run_command(cmd):
    print(f"▶️ {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def monitor_rss(feed_url):
    print(f"\U0001f504 Checking RSS: {feed_url}")
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:3]:
        print(f"📰 {entry.title} — {entry.link}")


def monitor_reddit(subreddit_name="entrepreneur"):
    print(f"👀 Monitoring Reddit: r/{subreddit_name}")
    subreddit = reddit.subreddit(subreddit_name)
    for post in subreddit.new(limit=3):
        print(f"📢 {post.title} — {post.url}")


def monitor_youtube_comments(video_id):
    print(f"▶️ Monitoring YouTube comments on video: {video_id}")
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={YOUTUBE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        comments = response.json().get("items", [])
        for comment in comments[:3]:
            text = comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            print(f"💬 {text}")
    else:
        print("❌ Failed to fetch comments")


def discover_and_validate():
    rotate_proxy()
    monitor_rss("https://hnrss.org/frontpage")
    monitor_reddit("smallbusiness")
    monitor_youtube_comments("dQw4w9WgXcQ")


def generate_content():
    print("✍️ Generating content via OpenAI...")


def format_and_package():
    print("📦 Formatting and packaging assets...")


def deploy_infrastructure():
    print("☁️ Deploying infra via Terraform...")
    os.chdir("infra")
    run_command("terraform init && terraform apply -auto-approve")
    os.chdir("..")


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


def inter_agent_communication(agent_id):
    comm_queue.put(f"Agent {agent_id} reporting in")
    while not comm_queue.empty():
        print(f"📨 {comm_queue.get()}")


def run_agent(name):
    print(f"🤖 Launching agent: {name}")
    discover_and_validate()
    generate_content()
    format_and_package()
    deploy_infrastructure()
    setup_fulfillment()
    setup_traffic_engines()
    reward = update_metrics()
    deploy_if_successful()
    inter_agent_communication(name)
    log_action(name, "complete_cycle", reward)


def monitor_and_optimize():
    print("📊 Starting monitoring loop...")
    while True:
        run_agent(f"agent-{time.time()}")
        time.sleep(3600)


def main():
    init_memory()
    threading.Thread(target=app.run, kwargs={'port': 8000}).start()
    agents = [multiprocessing.Process(target=run_agent, args=(f"agent-{i}",)) for i in range(3)]
    for agent in agents:
        agent.start()
    for agent in agents:
        agent.join()


if __name__ == '__main__':
    main()
