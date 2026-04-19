import os
import re
import requests
from requests.auth import HTTPBasicAuth

SN_INSTANCE = os.getenv("SN_INSTANCE")
SN_USER = os.getenv("SN_USER")
SN_PASSWORD = os.getenv("SN_PASSWORD")


def sn_get(table, query, fields, limit=10):
    url = f"{SN_INSTANCE}/api/now/table/{table}"

    res = requests.get(
        url,
        auth=HTTPBasicAuth(SN_USER, SN_PASSWORD),
        params={
            "sysparm_query": query,
            "sysparm_fields": fields,
            "sysparm_limit": limit
        }
    )

    res.raise_for_status()
    return res.json()["result"]


def answer_live_query(question):
    inc = re.search(r"(INC\d+)", question, re.I)

    if inc:
        num = inc.group(1)

        data = sn_get(
            "incident",
            f"number={num}",
            "number,state,priority,short_description"
        )

        if not data:
            return {"answer": "No record found", "records": []}

        r = data[0]

        return {
            "answer": f"{r['number']} is {r['state']} (P{r['priority']})",
            "records": data
        }

    if "how many" in question.lower() and "p1" in question.lower():
        data = sn_get(
            "incident",
            "priority=1^active=true",
            "number",
            limit=100
        )

        return {
            "answer": f"{len(data)} active P1 incidents",
            "records": data
        }

    return {
        "answer": "Live query not supported yet",
        "records": []
    }