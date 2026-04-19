import re


def clean_html(raw):
    if not raw:
        return ""
    return re.sub('<.*?>', '', raw)


def chunk_text(text, size=700, overlap=120):
    chunks = []
    start = 0

    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap

    return chunks


def tokenize(text):
    return re.findall(r"\w+", text.lower())