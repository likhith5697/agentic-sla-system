# app/services/hybrid_service.py
from app.services.knowledge_service import answer_knowledge_query
from app.services.live_data_service import answer_live_query

def answer_hybrid_query(question: str):
    kb = answer_knowledge_query(question)
    live = answer_live_query(question)

    answer = (
        f"{kb['answer']}\n\n"
        f"Live data:\n{live['answer']}"
    )

    return {
        "answer": answer,
        "sources": kb.get("sources", []),
        "records": live.get("records", [])
    }