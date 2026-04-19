from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



import chromadb

chroma_client = chromadb.PersistentClient(path="/data/chroma")




class Query(BaseModel):
    question: str


def embed_query(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


@app.get("/")
def health():
    return {"status": "running"}


@app.post("/ask")
def ask(query: Query):
    
    collection = chroma_client.get_or_create_collection(name="snow_kb")
    
    print("\n[DEBUG] Incoming question:", query.question)

    # Step 1: embed
    query_embedding = embed_query(query.question)

    # Step 2: search (include distances + metadata)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        include=["documents", "distances", "metadatas"]
    )

    print("\n[DEBUG] Raw results:", results)

    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    print(f"[DEBUG] Retrieved docs count: {len(docs)}")

    # 🔥 FILTER BAD MATCHES
    # filtered_docs = []
    # for doc, dist, meta in zip(docs, distances, metas):
    #     print(f"[DEBUG] Distance: {dist} | Title: {meta.get('title')}")
        
    #     if dist < 1.2:   # 👈 threshold (tune later)
    #         filtered_docs.append(doc)
    filtered_docs = docs

    if not filtered_docs:
        return {
            "answer": "No relevant data found.",
            "sources": []
        }

    context = "\n\n".join(filtered_docs)

    print("\n[DEBUG] Context passed to LLM:\n", context[:500])

    # 🔥 STRONG PROMPT
    prompt = f"""
You are an SLA assistant.

Answer ONLY from the context below.
If answer is not clearly present, say: "No data found".

Context:
{context}

Question:
{query.question}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "Strict SLA assistant. No guessing."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": filtered_docs
    }