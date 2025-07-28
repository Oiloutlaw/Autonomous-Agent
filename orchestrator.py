import os
import sys
import time
import subprocess
import openai
import praw
from dotenv import load_dotenv
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from utils.platform_utils import (
    get_secrets_dir, normalize_path, run_command, 
    get_terraform_command, format_shell_command
)

# Load `.env` if present
load_dotenv()

# Secret names and retrieval paths
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
    'agent_email'
]
SECRETS_DIR = get_secrets_dir()

def load_secret(name):
    env_key = name.upper()
    if env_key in os.environ:
        return os.getenv(env_key)
    path = normalize_path(os.path.join(SECRETS_DIR, name))
    if os.path.isfile(path):
        with open(path, 'r') as f:
            return f.read().strip()
    return None

# Retrieve credentials
openai.api_key = load_secret('openai_api_key')
os.environ['GITHUB_TOKEN'] = load_secret('github_token')
os.environ['STRIPE_KEY'] = load_secret('stripe_secret_key')

EMAIL = load_secret('agent_email') or os.getenv('AGENT_EMAIL')

# Reddit PRAW Setup
reddit = praw.Reddit(
    client_id=load_secret('reddit_client_id'),
    client_secret=load_secret('reddit_client_secret'),
    user_agent=load_secret('reddit_user_agent')
)

def run_shell_command(cmd):
    """Wrapper for shell commands - use run_command from platform_utils instead"""
    return run_command(cmd)

def discover_and_validate():
    print("🔍 Discovering niches...")

def generate_content():
    print("✍️ Generating content via OpenAI...")

def format_and_package():
    print("📦 Formatting and packaging assets...")

def deploy_infrastructure():
    print("☁️ Deploying infra via Terraform...")
    
    try:
        terraform_cmd = get_terraform_command()
    except RuntimeError as e:
        print(f"❌ {e}")
        return
    
    original_dir = os.getcwd()
    try:
        os.chdir("infra")
        commands = [
            f"{terraform_cmd} init",
            f"{terraform_cmd} apply -auto-approve"
        ]
        shell_cmd = format_shell_command(commands)
        run_command(shell_cmd)
    finally:
        os.chdir(original_dir)

def setup_fulfillment():
    print("💳 Setting up Stripe and emailing via AWS SES...")

def setup_traffic_engines():
    print("🚀 Configuring SEO & publishing pipelines...")

def monitor_and_optimize():
    print("📈 Starting monitoring loop...")
    while True:
        time.sleep(3600)

def main():
    discover_and_validate()
    generate_content()
    format_and_package()
    deploy_infrastructure()
    setup_fulfillment()
    setup_traffic_engines()
    monitor_and_optimize()

if __name__ == '__main__':
    main()
