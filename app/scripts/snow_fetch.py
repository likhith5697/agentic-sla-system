import os
import requests
from requests.auth import HTTPBasicAuth

SN_INSTANCE = os.getenv("SN_INSTANCE")
SN_USER = os.getenv("SN_USER")
SN_PASSWORD = os.getenv("SN_PASSWORD")
SN_KB_NAME = os.getenv("SN_KB_NAME")


def fetch_articles():
    url = f"{SN_INSTANCE}/api/now/table/kb_knowledge"

    query = f"workflow_state=published^kb_knowledge_base.title={SN_KB_NAME}"

    res = requests.get(
        url,
        auth=HTTPBasicAuth(SN_USER, SN_PASSWORD),
        params={
            "sysparm_query": query,
            "sysparm_fields": "sys_id,number,short_description,text"
        }
    )

    res.raise_for_status()
    return res.json()["result"]