import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_schema(system_design):

    prompt = f"""
    You are a senior software architect.

    Convert the following system design into:

    1. UI Schema
    2. API Schema
    3. Database Schema
    4. Auth Rules

    Return ONLY valid JSON.

    Format:

    {{
      "ui_schema": {{}},
      "api_schema": {{}},
      "db_schema": {{}},
      "auth_rules": {{}}
    }}

    System Design:
    {system_design}
    """

    response = model.generate_content(prompt)

    text = response.text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1)

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    print("\nRAW SCHEMA RESPONSE:\n")
    print(text)

    return text