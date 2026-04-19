# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel

from app.router import classify_intent
from app.services.knowledge_service import answer_knowledge_query
from app.services.live_data_service import answer_live_query
from app.services.hybrid_service import answer_hybrid_query

app = FastAPI()

class Query(BaseModel):
    question: str

@app.get("/")
def health():
    return {"status": "running"}

@app.post("/ask")
def ask(query: Query):
    intent = classify_intent(query.question)

    if intent == "knowledge_query":
        result = answer_knowledge_query(query.question)
    elif intent == "live_table_query":
        result = answer_live_query(query.question)
    else:
        result = answer_hybrid_query(query.question)

    return {
        "intent": intent,
        "answer": result["answer"],
        "sources": result.get("sources", []),
        "records": result.get("records", [])
    }