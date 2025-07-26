import os
import sys
sys.path.append("/home/ubuntu/repos/Autonomous-Agent/agents")
from youtube_uploader import execute_youtube_upload

def log_action(agent, action, reward=0):
    """Import the logging function from the main launcher"""
    sys.path.append("/home/ubuntu/repos/Autonomous-Agent")
    from SelfHealingLauncher import log_action as main_log_action
    main_log_action(agent, action, reward)

class UploaderAgent:
    def execute_task(self, video_path):
        """Main entry point for CrewAI Agent integration"""
        try:
            log_action("uploader", f"Processing upload request for: {video_path}")
            result = execute_youtube_upload(video_path)
            log_action("uploader", "Upload task completed", 1)
            return result
        except Exception as e:
            log_action("uploader", f"Upload task failed: {str(e)}", -1)
            return f"Error in upload task: {str(e)}"

uploader_agent = UploaderAgent()

def execute_upload_task(video_path):
    """Entry point for CrewAI Agent"""
    return uploader_agent.execute_task(video_path)

if __name__ == "__main__":
    print("🚀 Agent active: uploader.py")
