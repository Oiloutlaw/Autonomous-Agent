import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()

def log_action(agent, action, reward=0):
    """Import the logging function from the main launcher"""
    import sys
    sys.path.append("/home/ubuntu/repos/Autonomous-Agent")
    from SelfHealingLauncher import log_action as main_log_action
    main_log_action(agent, action, reward)

class YouTubeUploaderAgent:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY not found in environment variables")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
    
    def execute_task(self, video_path, title="AI Generated Video", description="Created by Autonomous Agent"):
        """Main entry point for CrewAI Agent integration"""
        try:
            if not os.path.exists(video_path):
                log_action("youtube_uploader", f"Video file not found: {video_path}", -1)
                return f"Error: Video file not found at {video_path}"
            
            log_action("youtube_uploader", f"Starting upload: {video_path}")
            
            log_action("youtube_uploader", "Upload simulation completed (OAuth required for real uploads)", 1)
            return f"YouTube video prepared for upload: {title}"
            
        except Exception as e:
            log_action("youtube_uploader", f"Upload failed: {str(e)}", -1)
            return f"Error uploading video: {str(e)}"
    
    def prepare_metadata(self, title, description, tags=None):
        """Prepare video metadata for upload"""
        if tags is None:
            tags = ["AI", "automation", "content creation", "YouTube Shorts"]
        
        return {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # People & Blogs
            },
            'status': {
                'privacyStatus': 'public'
            }
        }

youtube_uploader_agent = YouTubeUploaderAgent()

def execute_youtube_upload(video_path, title="AI Generated Video", description="Created by Autonomous Agent"):
    """Entry point for CrewAI Agent"""
    return youtube_uploader_agent.execute_task(video_path, title, description)

if __name__ == "__main__":
    print("🚀 Agent active: youtube_uploader.py")
