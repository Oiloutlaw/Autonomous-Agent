#!/usr/bin/env python3
"""
Test script to demonstrate video generation with the fixed ElevenLabs API
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from utils.platform_utils import get_repo_dir

repo_dir = get_repo_dir()
agents_dir = os.path.join(repo_dir, 'agents')
if agents_dir not in sys.path:
    sys.path.append(agents_dir)

def test_video_generation():
    """Test video generation with a simple script"""
    
    required_keys = ['OPENAI_API_KEY', 'ELEVENLABS_API_KEY', 'MODELSLAB_API_KEY']
    missing_keys = []
    
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        print("❌ Missing required API keys in .env file:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nPlease add these keys to your .env file to test video generation.")
        return False
    
    try:
        from video_creator import execute_video_creation
        print("✅ VideoCreator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import VideoCreator: {e}")
        return False
    
    test_script = """
    Welcome to the future of AI automation! 
    
    Today we're exploring how artificial intelligence can create entire YouTube channels automatically.
    
    From trending topics to viral videos, AI is revolutionizing content creation.
    
    The possibilities are endless when technology meets creativity!
    """
    
    print("\n🎬 Testing video generation with sample script...")
    print("=" * 50)
    
    try:
        result = execute_video_creation(test_script)
        print(f"✅ Video generation result: {result}")
        return True
    except Exception as e:
        print(f"❌ Video generation failed: {e}")
        print("\nThis could be due to:")
        print("- Invalid API keys")
        print("- Network connectivity issues")
        print("- Missing ffmpeg installation")
        print("- API rate limits or quota exceeded")
        return False

def main():
    print("Testing Video Generation with Fixed ElevenLabs API")
    print("=" * 60)
    
    success = test_video_generation()
    
    print("=" * 60)
    if success:
        print("🎉 Video generation test completed!")
        print("Check the 'output' directory for generated files.")
    else:
        print("💥 Video generation test failed.")
        print("Make sure your .env file has valid API keys.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
