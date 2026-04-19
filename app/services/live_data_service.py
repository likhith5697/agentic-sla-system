import os
import requests
from requests.auth import HTTPBasicAuth
from app.services.query_parser import parse_live_query

SN_INSTANCE = os.getenv("SN_INSTANCE")
SN_USER = os.getenv("SN_USER")
SN_PASSWORD = os.getenv("SN_PASSWORD")


def sn_get(table: str, query: str, fields: str, limit: int = 50):
    url = f"{SN_INSTANCE}/api/now/table/{table}"

    res = requests.get(
        url,
        auth=HTTPBasicAuth(SN_USER, SN_PASSWORD),
        params={
            "sysparm_query": query,
            "sysparm_fields": fields,
            "sysparm_limit": limit,
            "sysparm_display_value": "true",
        },
        timeout=30,
    )

    res.raise_for_status()
    return res.json()["result"]


def build_query(filters: dict) -> str:
    q = []

    if "priority" in filters and filters["priority"]:
        q.append(f"priority={filters['priority']}")

    # default active=true for dashboard/live questions unless explicitly set
    if "active" in filters:
        q.append(f"active={'true' if filters['active'] else 'false'}")
    else:
        q.append("active=true")

    return "^".join(q)


def get_display(val):
    if isinstance(val, dict):
        return val.get("display_value") or val.get("value") or ""
    return val or ""


def clean_incident_record(record: dict) -> dict:
    return {
        "number": record.get("number", ""),
        "short_description": record.get("short_description", ""),
        "state": get_display(record.get("state")),
        "priority": get_display(record.get("priority")),
        "assigned_to": get_display(record.get("assigned_to")),
        "assignment_group": get_display(record.get("assignment_group")),
    }


def format_count_answer(question: str, incidents: list[dict], breached: bool) -> str:
    if breached:
        return f"{len(incidents)} active incidents matched and have breached SLA."

    return f"{len(incidents)} active incidents matched."


def format_list_answer(question: str, incidents: list[dict], breached: bool) -> str:
    if not incidents:
        return "No matching records found."

    nums = ", ".join(i["number"] for i in incidents[:5])

    if breached:
        return f"Found {len(incidents)} breached active incidents. Top records: {nums}."

    return f"Found {len(incidents)} matching active incidents. Top records: {nums}."


def answer_live_query(question: str):
    parsed = parse_live_query(question)

    filters = parsed.get("filters", {})
    agg = parsed.get("aggregation", "list")
    requested_table = parsed.get("table", "incident")

    # For now we support incident-led live answers.
    # task_sla is used as supporting join data for breached queries.
    if requested_table not in ["incident", "task_sla"]:
        requested_table = "incident"

    incident_query = build_query(filters)

    incidents = sn_get(
        "incident",
        incident_query,
        "number,priority,state,short_description,assigned_to,assignment_group",
        50,
    )

    # SLA join only when needed
    if filters.get("breached"):
        slas = sn_get(
            "task_sla",
            "has_breached=true^active=true",
            "task",
            100,
        )

        breached_ids = set()
        for s in slas:
            task = s.get("task")
            task_value = get_display(task)
            if task_value:
                breached_ids.add(task_value)

        incidents = [i for i in incidents if i.get("number") in breached_ids]

    cleaned_records = [clean_incident_record(i) for i in incidents[:10]]

    if agg == "count":
        return {
            "answer": format_count_answer(question, incidents, filters.get("breached", False)),
            "records": cleaned_records,
        }

    return {
        "answer": format_list_answer(question, incidents, filters.get("breached", False)),
        "records": cleaned_records,
    }