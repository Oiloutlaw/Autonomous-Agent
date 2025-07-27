#!/usr/bin/env python3
"""
Launcher script for Unified Autonomous Agent System
Handles environment setup and error handling for double-click execution
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        'OPENAI_API_KEY',
        'YOUTUBE_API_KEY',
        'STRIPE_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment")
        return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    try:
        print("📦 Installing dependencies...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main launcher function"""
    print("🚀 Autonomous Agent Launcher")
    print("=" * 40)
    
    if not check_python_version():
        input("Press Enter to exit...")
        return 1
    
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    env_file = script_dir / '.env'
    if not env_file.exists():
        print("⚠️ .env file not found")
        print("Please copy .env.example to .env and configure your API keys")
        input("Press Enter to exit...")
        return 1
    
    if not check_environment():
        input("Press Enter to exit...")
        return 1
    
    requirements_file = script_dir / 'requirements.txt'
    if requirements_file.exists():
        if not install_dependencies():
            input("Press Enter to exit...")
            return 1
    
    try:
        print("🤖 Starting Unified Autonomous Agent System...")
        print("Press Ctrl+C to stop")
        print("=" * 40)
        
        main_script = script_dir / 'main.py'
        subprocess.run([sys.executable, str(main_script)])
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping agent system...")
    except Exception as e:
        print(f"❌ Error running agent system: {e}")
        input("Press Enter to exit...")
        return 1
    
    print("✅ Agent system stopped")
    return 0

if __name__ == "__main__":
    sys.exit(main())
