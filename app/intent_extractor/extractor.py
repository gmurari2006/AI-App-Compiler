import json
from app.llm.groq_client import client


def extract_intent(user_input):

    prompt = f"""
    Analyze the following app idea and return ONLY valid JSON.

    Format:

    {{
      "app_type": "",
      "features": [],
      "roles": []
    }}

    App Idea:
    {user_input}
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

        print("\nRAW RESPONSE:\n")
        print(text)

        return json.loads(text)

    except Exception as e:

        print(f"\nIntent extraction failed:\n{e}")

        return {
            "app_type": "Unknown",
            "features": [],
            "roles": []
        }