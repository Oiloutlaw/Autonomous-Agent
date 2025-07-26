import os
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def write_script(topic_title, topic_description):
    prompt = f"""
You are a creative YouTube Shorts scriptwriter. Write a fast-paced, highly engaging 60-second script for a YouTube Short.

Topic: "{topic_title}"
Description: {topic_description}

Make it punchy, emotional, and structured for voiceover narration. Use short sentences and hooks. End with a call to action.
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a viral short-form scriptwriter for YouTube."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=500
    )

    script = response.choices[0].message.content.strip()
    print("📜 Generated Script:\n" + script)
    return script

if __name__ == "__main__":
    write_script(
        topic_title="Rise and Grind - Morning Motivation Rituals",
        topic_description="In this trend, successful entrepreneurs take viewers through their morning routines, highlighting the motivational rituals that start their productive day."
    )
