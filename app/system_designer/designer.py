import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def design_system(intent_data):

    prompt = f"""
    You are a software architect.

    Convert the following intent into application architecture.

    Return ONLY valid JSON.

    Format:

    {{
      "pages": [],
      "entities": [],
      "roles": []
    }}

    Intent:
    {intent_data}
    """

    response = model.generate_content(prompt)

    text = response.text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1)

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    return json.loads(text)