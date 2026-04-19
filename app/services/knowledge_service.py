import chromadb
from collections import Counter
from app.utils.embeddings import embed
from app.utils.text import tokenize
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="/data/chroma")
collection = chroma_client.get_or_create_collection("snow_kb_chunks")


# -------- Retrieval --------

def lexical_score(query, doc):
    q_terms = tokenize(query)
    d_terms = tokenize(doc)

    if not d_terms:
        return 0

    counts = Counter(d_terms)
    return sum(counts[t] for t in q_terms) / len(d_terms)


def get_all_docs():
    data = collection.get(include=["documents", "metadatas"])
    return list(zip(data["documents"], data["metadatas"]))


def dense_search(query):
    emb = embed(query)

    results = collection.query(
        query_embeddings=[emb],
        n_results=10,
        include=["documents", "distances", "metadatas"]
    )

    docs = results["documents"][0]
    dists = results["distances"][0]
    metas = results["metadatas"][0]

    return [
        {
            "doc": d,
            "meta": m,
            "score": 1 / (1 + dist)
        }
        for d, dist, m in zip(docs, dists, metas)
    ]


def lexical_search(query):
    docs = get_all_docs()

    scored = []
    for doc, meta in docs:
        scored.append({
            "doc": doc,
            "meta": meta,
            "score": lexical_score(query, doc)
        })

    return sorted(scored, key=lambda x: x["score"], reverse=True)[:10]


def fuse(query):
    dense = dense_search(query)
    lex = lexical_search(query)

    merged = {}

    def add(items):
        for rank, item in enumerate(items, 1):
            key = item["meta"]["chunk_id"]

            if key not in merged:
                merged[key] = item

            merged[key]["score"] += 2 / (60 + rank)

    add(dense)
    add(lex)

    return sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:6]


# -------- LLM --------

def build_answer(query, chunks):
    context = "\n\n".join(
        f"[{i+1}] {c['meta']['title']} ({c['meta']['number']}):\n{c['doc']}"
        for i, c in enumerate(chunks)
    )

    prompt = f"""
Answer ONLY from context.
If missing, say: No data found.

Context:
{context}

Question:
{query}
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return res.choices[0].message.content.strip()


def answer_knowledge_query(query):
    chunks = fuse(query)

    # 🔥 deduplicate by KB number
    seen = set()
    clean_chunks = []

    for c in chunks:
        kb = c["meta"]["number"]
        if kb not in seen:
            clean_chunks.append(c)
            seen.add(kb)

    # 🔥 keep only top 2
    top_chunks = clean_chunks[:2]

    answer = build_answer(query, top_chunks)

    sources = [
        {
            "kb": c["meta"]["number"],
            "title": c["meta"]["title"]
        }
        for c in top_chunks
    ]

    return {
        "answer": answer,
        "sources": sources
    }