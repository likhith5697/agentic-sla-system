import re

# 🔥 LIVE (tables / metrics / real-time)
LIVE_PATTERNS = [
    r"\bINC\d+\b",
    r"\bincident(s)?\b",
    r"\bbreach(ed)?\b",
    r"\bactive\b",
    r"\bopen\b",
    r"\bcurrent\b",
    r"\bhow many\b",
    r"\bcount\b",
    r"\blist\b",
    r"\bshow\b",
    r"\bassigned\b",
    r"\bowner\b",
    r"\bwho is\b",
    r"\bpriority\b",
]

# 🔥 KNOWLEDGE (KB / SLA definitions)
KNOWLEDGE_PATTERNS = [
    r"\bwhat is\b",
    r"\bhow does\b",
    r"\bpolicy\b",
    r"\bprocess\b",
    r"\bdefinition\b",
    r"\bwhat happens\b",
    r"\bsla details\b",
    r"\bexplain\b",
]

def match_any(text, patterns):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)



def classify_intent(question: str) -> str:
    q = question.lower()

    # 🔥 HARD OVERRIDE (MOST IMPORTANT FIX)
    if re.search(r"\binc\d+\b", q, re.IGNORECASE):
        return "live_table_query"

    live = match_any(q, LIVE_PATTERNS)
    knowledge = match_any(q, KNOWLEDGE_PATTERNS)

    if live and knowledge:
        return "hybrid_query"

    if live:
        return "live_table_query"

    return "knowledge_query"