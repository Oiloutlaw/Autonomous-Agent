import os
import openai
import requests
import time
import subprocess
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

try:
    from elevenlabs.client import ElevenLabs

    ELEVENLABS_AVAILABLE = True
except ImportError:
    print(
        "⚠️ ElevenLabs module not available. Voice generation features will be disabled."
    )
    ElevenLabs = None
    ELEVENLABS_AVAILABLE = False

load_dotenv()


def log_action(agent, action, reward=0):
    """Import the logging function from the main launcher"""
    import sys

    sys.path.append("/home/ubuntu/repos/Autonomous-Agent")
    from SelfHealingLauncher import log_action as main_log_action

    main_log_action(agent, action, reward)


class VideoCreatorAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.eleven_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_client = (
            ElevenLabs(api_key=self.eleven_key) if ELEVENLABS_AVAILABLE else None
        )
        self.stability_key = os.getenv("MODELSLAB_API_KEY")
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

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
        """Generate voiceover using ElevenLabs"""
        if not ELEVENLABS_AVAILABLE or not self.elevenlabs_client:
            print("⚠️ ElevenLabs not available, skipping voiceover generation")
            out_path = os.path.join(self.output_dir, filename)
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=duration=3",
                "-c:a",
                "aac",
                out_path,
            ]
            subprocess.run(cmd, check=True)
            return out_path

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
        for i, (img, audio) in enumerate(inputs):
            output_path = os.path.join(self.output_dir, f"segment_{i:02d}.mp4")
            cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                img,
                "-i",
                audio,
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

        with open(os.path.join(self.output_dir, "segments.txt"), "w") as f:
            for seg in segment_paths:
                f.write(f"file '{os.path.abspath(seg)}'\n")

        final_video = os.path.join(self.output_dir, "final_video.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            os.path.join(self.output_dir, "segments.txt"),
            "-c",
            "copy",
            final_video,
        ]
        subprocess.run(cmd, check=True)

        return final_video


video_creator_agent = VideoCreatorAgent()


def execute_video_creation(script_text):
    """Entry point for CrewAI Agent"""
    return video_creator_agent.execute_task(script_text)


if __name__ == "__main__":
    print("🚀 Agent active: video_creator.py")
