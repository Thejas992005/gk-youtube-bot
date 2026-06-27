import requests
import json
import os
import random
import time

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

GK_TOPICS = [
    "World Geography", "Indian History", "Science & Technology",
    "Sports", "Famous Personalities", "Current Affairs",
    "Space & Universe", "Animals & Nature", "Art & Culture",
    "Economics & Finance", "World History", "Politics"
]

def generate_question(retries=5):
    topic = random.choice(GK_TOPICS)

    prompt = f"""Generate a General Knowledge MCQ question about {topic}.
Return ONLY a JSON object in this exact format, no extra text, no markdown backticks:
{{
  "question": "Your question here?",
  "options": {{
    "A": "First option",
    "B": "Second option",
    "C": "Third option",
    "D": "Fourth option"
  }},
  "answer": "A",
  "explanation": "Brief explanation why this is correct.",
  "topic": "{topic}"
}}
Make sure the question is interesting, factual, and the answer is accurate."""

    for attempt in range(retries):
        try:
            time.sleep(2)

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://gk-youtube-bot.railway.app",
                    "X-Title": "GK YouTube Bot"
                },
                json={
                    "model": "meta-llama/llama-3.1-8b-instruct:free",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )

            if response.status_code != 200:
                raise Exception(f"API error {response.status_code}: {response.text}")

            data = response.json()
            text = data["choices"][0]["message"]["content"].strip()

            # Clean up markdown if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            # Find JSON object in text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                text = text[start:end]

            result = json.loads(text)
            print(f"✅ Question generated: {result['question'][:60]}...")
            return result

        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            wait_time = (attempt + 1) * 10
            print(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)

    raise Exception("Failed to generate question after all retries")


if __name__ == "__main__":
    q = generate_question()
    print(json.dumps(q, indent=2))
