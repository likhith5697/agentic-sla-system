import re

LIVE_PATTERNS = [
    r"\bINC\d+\b",
    r"\bopen incidents?\b",
    r"\bbreached\b",
    r"\bactive sla\b",
    r"\bcurrent\b",
    r"\bhow many\b",
    r"\blist incidents?\b",
]

KNOWLEDGE_PATTERNS = [
    r"\bwhat is\b",
    r"\bhow does\b",
    r"\bpolicy\b",
    r"\bprocess\b",
    r"\bwhat happens if\b",
    r"\bsla\b",
]


def match_any(text, patterns):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def classify_intent(question: str) -> str:
    live = match_any(question, LIVE_PATTERNS)
    knowledge = match_any(question, KNOWLEDGE_PATTERNS)

    if live and knowledge:
        return "hybrid_query"
    if live:
        return "live_table_query"
    return "knowledge_query"