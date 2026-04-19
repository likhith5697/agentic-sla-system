from openai import OpenAI
import os
import json
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def clean_json(raw: str):
    # 🔥 remove ```json ``` or ``` wrappers
    raw = re.sub(r"```json", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```", "", raw)
    return raw.strip()


def parse_live_query(question: str):
    prompt = f"""
Convert the user question into a structured JSON query.

Return ONLY JSON.

Schema:
{{
  "table": "incident",
  "filters": {{
    "priority": "1",
    "active": true,
    "breached": true
  }},
  "aggregation": "count"
}}

Rules:
- P1 = priority 1
- breached = SLA breached
- how many = count

Question:
{question}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()

    print("\n[DEBUG RAW]:", raw)

    cleaned = clean_json(raw)

    print("\n[DEBUG CLEANED]:", cleaned)

    try:
        return json.loads(cleaned)
    except Exception as e:
        print("[ERROR PARSE]:", e)

        # 🔥 fallback (safe default)
        return {
            "table": "incident",
            "filters": {
                "priority": "1",
                "breached": True
            },
            "aggregation": "count"
        }