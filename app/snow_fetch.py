import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()


class Config:
    INSTANCE = os.getenv("SN_INSTANCE")
    USER = os.getenv("SN_USER")
    PASSWORD = os.getenv("SN_PASSWORD")
    KB_NAME = os.getenv("SN_KB_NAME")
    LIMIT = int(os.getenv("SN_LIMIT", 50))


def fetch_articles():
    url = f"{Config.INSTANCE}/api/now/table/kb_knowledge"

    query = f"workflow_state=published^kb_knowledge_base.title={Config.KB_NAME}"

    print("\n[DEBUG] Fetching articles...")
    print(f"[DEBUG] KB: {Config.KB_NAME}")

    params = {
        "sysparm_query": query,
        "sysparm_fields": "sys_id,number,short_description,text",
        "sysparm_limit": Config.LIMIT
    }

    response = requests.get(
        url,
        auth=HTTPBasicAuth(Config.USER, Config.PASSWORD),
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()["result"]

    print(f"[DEBUG] Found {len(data)} articles")

    return data