import json
from app.llm.groq_client import client


def design_system(intent):

    prompt = f"""
    You are a senior software architect.

    Based on the following intent, generate a system design.

    Return ONLY valid JSON.

    Format:

    {{
        "pages": [],
        "entities": [],
        "roles": []
    }}

    Intent:
    {intent}
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

        text = response.choices[0].message.content.strip()

        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        print("\nSYSTEM DESIGN:\n")
        print(text)

        return json.loads(text)

    except Exception as e:

        print(f"\nSystem design failed:\n{e}")

        return {
            "pages": [],
            "entities": [],
            "roles": []
        }