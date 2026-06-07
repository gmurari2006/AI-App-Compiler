import json
from app.llm.groq_client import client


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

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        text = response.choices[0].message.content

        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        print("\nRAW SCHEMA RESPONSE:\n")
        print(text)

        return json.loads(text)

    except Exception as e:

        print(f"\nSchema generation failed:\n{e}")

        return {
            "ui_schema": {},
            "api_schema": {},
            "db_schema": {},
            "auth_rules": {}
        }