import os
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_thumbnail_idea(title, description):
    prompt = f"""
You're an expert YouTube thumbnail designer. Based on the title and video concept below, suggest an attention-grabbing thumbnail idea for a YouTube Short.

Title: "{title}"
Description: {description}

Describe:
- What text should be shown on the thumbnail (3-5 words max)
- What visual elements should be included (person, object, background)
- What emotion or tone it should convey (e.g., curiosity, urgency, awe)
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're an expert in YouTube thumbnail design for viral Shorts."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    thumbnail_concept = response.choices[0].message.content.strip()
    print("🖼️ Thumbnail Concept:\n" + thumbnail_concept)
    return thumbnail_concept

if __name__ == "__main__":
    generate_thumbnail_idea(
        title="Rise and Grind - Morning Motivation Rituals",
        description="Successful entrepreneurs share their morning routines that set them up for a high-performance day."
    )
