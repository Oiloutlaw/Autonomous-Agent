import os
import sys
import openai
import requests
import time
import subprocess
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.platform_utils import (
    get_ffmpeg_command, normalize_path, run_command, 
    ensure_directory, get_repo_dir
)

def safe_import_elevenlabs():
    """Safely import ElevenLabs with proper error handling for threading context"""
    try:
        from elevenlabs.client import ElevenLabs
        return True, ElevenLabs
    except ImportError as e:
        print(f"⚠️ ElevenLabs import failed: {e}")
        return False, None
    except Exception as e:
        print(f"⚠️ ElevenLabs import error: {e}")
        return False, None

ELEVENLABS_AVAILABLE, ElevenLabs = safe_import_elevenlabs()

load_dotenv()


def log_action(agent, action, reward=0):
    """Import the logging function from the main launcher"""
    repo_dir = get_repo_dir()
    if repo_dir not in sys.path:
        sys.path.append(repo_dir)
    
    try:
        from SelfHealingLauncher import log_action as main_log_action
        main_log_action(agent, action, reward)
    except ImportError as e:
        print(f"⚠️ Could not import logging function: {e}")
        print(f"[{agent}] {action} (Reward: {reward})")


class VideoCreatorAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.eleven_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_client = (
            ElevenLabs(api_key=self.eleven_key) if ELEVENLABS_AVAILABLE and ElevenLabs and self.eleven_key else None
        )
        self.stability_key = os.getenv("MODELSLAB_API_KEY")
        self.output_dir = normalize_path("output")
        ensure_directory(self.output_dir)

    def execute_task(self, script_text):
        """Main entry point for CrewAI Agent integration"""
        try:
            log_action("video_creator", "Starting video creation process")

            production_plan = self.break_script_into_scenes(script_text)
            scenes = self.parse_scenes(production_plan)

            if not scenes:
                log_action("video_creator", "No scenes parsed from script", -1)
                return "Error: Could not parse scenes from script"

            video_path = self.create_video(scenes)
            log_action("video_creator", f"Video created successfully: {video_path}", 1)
            return f"Short video file created: {video_path}"

        except Exception as e:
            log_action("video_creator", f"Video creation failed: {str(e)}", -1)
            return f"Error creating video: {str(e)}"

    def break_script_into_scenes(self, script_text):
        """Convert script to production plan using GPT-4"""
        prompt = f"""Break this YouTube Shorts script into a shot-by-shot production plan.
For each shot, include:
- Narration: (1 sentence max)
- Visual: (brief description)
- Prompt: (image generation prompt)

Format each shot like this:
Shot X:
Narration: [text here]
Visual: [description here]  
Prompt: [image prompt here]

SCRIPT:
{script_text}"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
        )
        return response.choices[0].message.content

    def parse_scenes(self, production_plan):
        """Parse the production plan into scene objects"""
        scenes = []
        current_scene = {}

        for line in production_plan.split("\n"):
            line = line.strip()
            if line.startswith("Narration:"):
                current_scene["narration"] = line.replace("Narration:", "").strip()
            elif line.startswith("Prompt:"):
                current_scene["image_prompt"] = line.replace("Prompt:", "").strip()
                if "narration" in current_scene and "image_prompt" in current_scene:
                    scenes.append(current_scene.copy())
                    current_scene = {}

        return scenes

    def generate_image(self, prompt_text, idx):
        """Generate image using ModelsLab API"""
        stable_url = "https://modelslab.com/api/v6/realtime/text2img"
        payload = {
            "key": self.stability_key,
            "prompt": prompt_text,
            "negative_prompt": "bad quality",
            "width": "512",
            "height": "512",
            "samples": 1,
            "safety_checker": False,
            "seed": None,
            "base64": False,
            "webhook": None,
            "track_id": None,
        }

        response = requests.post(stable_url, json=payload)
        response.raise_for_status()
        data = response.json()

        if "output" in data and isinstance(data["output"], list):
            image_url = data["output"][0]
            img_data = requests.get(image_url).content
            img_path = os.path.join(self.output_dir, f"scene_{idx:02d}.png")
            with open(img_path, "wb") as f:
                f.write(img_data)
            return img_path
        else:
            raise ValueError("No output image received from Stable Diffusion API")

    def generate_voiceover(self, text, filename):
        """Generate voiceover using ElevenLabs with improved error handling"""
        if not self.eleven_key:
            print("❌ ElevenLabs API key not found")
            return self._create_silent_audio(filename, text)
        elif not ELEVENLABS_AVAILABLE or not self.elevenlabs_client:
            print("❌ ElevenLabs module not available")
            return self._create_silent_audio(filename, text)
        else:
            try:
                audio_generator = self.elevenlabs_client.text_to_speech.convert(
                    text=text,
                    voice_id="JBFqnCBsd6RMkjVDRZzb",
                    model_id="eleven_multilingual_v2",
                )

                out_path = os.path.join(self.output_dir, filename)
                with open(out_path, "wb") as f:
                    for chunk in audio_generator:
                        if isinstance(chunk, bytes):
                            f.write(chunk)
                return out_path
            except Exception as e:
                print(f"❌ ElevenLabs voiceover failed: {e}")
                return self._create_silent_audio(filename, text)

    def _create_silent_audio(self, filename, text):
        """Create silent audio as fallback"""
        out_path = normalize_path(os.path.join(self.output_dir, filename))
        try:
            ffmpeg_cmd = get_ffmpeg_command()
            duration = max(3, len(text.split()) * 0.5)
            cmd = [
                ffmpeg_cmd,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"anullsrc=duration={duration}",
                "-c:a",
                "aac",
                out_path,
            ]
            subprocess.run(cmd, check=True)
            return out_path
        except RuntimeError as e:
            print(f"❌ {e}")
            raise

    def create_video(self, scenes):
        """Create final video from scenes"""
        inputs = []
        for i, scene in enumerate(scenes):
            print(f"🎬 Scene {i+1}: {scene['narration']}")

            image_path = self.generate_image(scene["image_prompt"], i)
            audio_path = self.generate_voiceover(
                scene["narration"], f"audio_{i:02d}.mp3"
            )
            inputs.append((image_path, audio_path))

        segment_paths = []
        try:
            ffmpeg_cmd = get_ffmpeg_command()
        except RuntimeError as e:
            print(f"❌ {e}")
            raise
            
        for i, (img, audio) in enumerate(inputs):
            output_path = normalize_path(os.path.join(self.output_dir, f"segment_{i:02d}.mp4"))
            cmd = [
                ffmpeg_cmd,
                "-y",
                "-loop",
                "1",
                "-i",
                normalize_path(img),
                "-i",
                normalize_path(audio),
                "-c:v",
                "libx264",
                "-tune",
                "stillimage",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-pix_fmt",
                "yuv420p",
                output_path,
            ]
            subprocess.run(cmd, check=True)
            segment_paths.append(output_path)

        segments_file = normalize_path(os.path.join(self.output_dir, "segments.txt"))
        with open(segments_file, "w") as f:
            for seg in segment_paths:
                abs_path = os.path.abspath(seg).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")

        final_video = normalize_path(os.path.join(self.output_dir, "final_video.mp4"))
        try:
            ffmpeg_cmd = get_ffmpeg_command()
        except RuntimeError as e:
            print(f"❌ {e}")
            raise
            
        cmd = [
            ffmpeg_cmd,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            segments_file,
            "-c",
            "copy",
            final_video,
        ]
        subprocess.run(cmd, check=True)

        return final_video


def execute_video_creation(script_text):
    """Entry point for CrewAI Agent"""
    video_creator_agent = VideoCreatorAgent()
    return video_creator_agent.execute_task(script_text)

def generate_voiceover(text, output_file):
    """Standalone voiceover generation function for compatibility"""
    creator = VideoCreatorAgent()
    return creator.generate_voiceover(text, output_file)

def break_script_into_scenes(script):
    """Break script into scenes for compatibility"""
    creator = VideoCreatorAgent()
    return creator.break_script_into_scenes(script)

def create_video_from_scenes(scenes, output_file):
    """Create video from scenes for compatibility"""
    creator = VideoCreatorAgent()
    return creator.create_video(scenes)


if __name__ == "__main__":
    print("🚀 Agent active: video_creator.py")
