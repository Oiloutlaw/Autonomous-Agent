#!/usr/bin/env python3
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from utils.platform_utils import get_repo_dir

repo_dir = get_repo_dir()
agents_dir = os.path.join(repo_dir, 'agents')
if agents_dir not in sys.path:
    sys.path.append(agents_dir)

from video_creator import VideoCreatorAgent

def test_parsing():
    agent = VideoCreatorAgent()
    
    mock_plan = """Shot 1:
Narration: Each day, greatness GETS UP before sunrise.
Visual: Alarm clock ringing at 5 AM
Prompt: Vintage alarm clock ringing, early morning light, motivational atmosphere

Shot 2:
Narration: Morning rituals? They're not just habits.
Visual: Entrepreneur making coffee
Prompt: Professional person making coffee, modern kitchen, morning routine"""
    
    scenes = agent.parse_scenes(mock_plan)
    print(f"Parsed {len(scenes)} scenes:")
    for i, scene in enumerate(scenes):
        print(f"Scene {i+1}: '{scene['narration']}'")
        print(f"Prompt: '{scene['image_prompt']}'")

if __name__ == "__main__":
    test_parsing()
