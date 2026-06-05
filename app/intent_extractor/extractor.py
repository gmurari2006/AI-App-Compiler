import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def extract_intent(user_prompt):

    prompt = f"""
    Convert the following app request into JSON.

    Return ONLY valid JSON.

    Format:

    {{
      "app_type": "",
      "features": [],
      "roles": []
    }}

    User Request:
    {user_prompt}
    """

    response = model.generate_content(prompt)

    text = response.text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1)

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    return json.loads(text)