import os
import re
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from snow_fetch import fetch_articles

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

import chromadb

chroma_client = chromadb.PersistentClient(path="/data/chroma")
collection = chroma_client.get_or_create_collection(name="snow_kb")


def clean_html(raw_html):
    if not raw_html:
        return ""
    return re.sub('<.*?>', '', raw_html).strip()


def embed_text(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def ingest():
    articles = fetch_articles()

    print("\n[DEBUG] Starting ingestion...\n")

    for article in articles:
        raw = article.get("text")
        clean_text = clean_html(raw)

        text = clean_text if clean_text else article.get("short_description")

        print("-----")
        print(f"[DEBUG] Article: {article.get('short_description')}")
        print(f"[DEBUG] Raw length: {len(raw) if raw else 0}")
        print(f"[DEBUG] Clean length: {len(text)}")

        if not text or len(text) < 20:
            print("[WARNING] Skipping empty/weak article")
            continue

        embedding = embed_text(text)

        collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[{
                "title": article["short_description"],
                "number": article["number"]
            }],
            ids=[article["number"]]
        )

    

    print(f"\n[DEBUG] Total stored: {collection.count()}")
    print("\n[DEBUG] Ingestion complete\n")


if __name__ == "__main__":
    ingest()