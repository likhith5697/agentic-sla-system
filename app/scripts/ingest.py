import chromadb
from app.scripts.snow_fetch import fetch_articles
from app.utils.text import clean_html, chunk_text
from app.utils.embeddings import embed

client = chromadb.PersistentClient(path="/data/chroma")
collection = client.get_or_create_collection("snow_kb_chunks")


def ingest():
    articles = fetch_articles()

    for art in articles:
        text = clean_html(art["text"]) or art["short_description"]

        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            collection.add(
                documents=[chunk],
                embeddings=[embed(chunk)],
                metadatas=[{
                    "number": art["number"],
                    "title": art["short_description"],
                    "chunk_id": f"{art['number']}_{i}"
                }],
                ids=[f"{art['number']}_{i}"]
            )

    print("Ingestion complete:", collection.count())


if __name__ == "__main__":
    ingest()