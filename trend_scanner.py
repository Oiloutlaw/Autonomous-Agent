import os
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_viral_idea():
    prompt = (
        "Give me a list of 3 viral YouTube Shorts topics related to personal finance, motivation, "
        "or entrepreneurship that are trending right now. Include a title and 1-sentence description for each."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a viral trend analyst for YouTube content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=300
    )

    ideas = response.choices[0].message.content.strip()
    print("🔥 Viral Topic Ideas:\n" + ideas)
    return ideas

if __name__ == "__main__":
    generate_viral_idea()
