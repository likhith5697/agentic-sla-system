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
Convert the user question into structured JSON.

Return ONLY JSON.

Schema:
{{
  "table": "incident",
  "filters": {{
    "number": "INC0000000",
    "priority": "1",
    "active": true,
    "breached": true
  }},
  "aggregation": "count | list | single"
}}

Rules:
- If question contains INC number → use "number"
- If asking about specific incident → aggregation = "single"
- "how many" → count
- "list" → list
- "who is assigned" → single

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