"""Document ingestion and chunking for The Unofficial Guide RAG pipeline.

Stage 1 (Document Ingestion) and Stage 2 (Chunking) of the architecture:
reads raw .txt files from the documents folder and splits them into
fixed-size character chunks with overlap, preserving source attribution.
"""

import os

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


def load_documents(folder):
    """Read every .txt file in `folder` and return a list of document dicts.

    Each dict has:
      - text:   the full file contents
      - source: the filename (e.g. "prof_mills.txt")
    """
    documents = []
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(folder, filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        documents.append({"text": text, "source": filename})
    return documents


def chunk_documents(documents, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split each document's text into overlapping character chunks.

    Slides a window of `chunk_size` characters across each document, advancing
    by `chunk_size - overlap` each step so consecutive chunks share `overlap`
    characters. Each chunk dict carries the original source filename so
    attribution survives into the vector store.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    step = chunk_size - overlap
    chunks = []
    for doc in documents:
        text = doc["text"]
        source = doc["source"]
        for start in range(0, len(text), step):
            chunk_text = text[start:start + chunk_size]
            if not chunk_text.strip():
                continue
            chunks.append({"text": chunk_text, "source": source})
            # Stop once the window reaches the end of the text.
            if start + chunk_size >= len(text):
                break
    return chunks


if __name__ == "__main__":
    folder = "documents"
    documents = load_documents(folder)
    chunks = chunk_documents(documents)

    print(f"Loaded {len(documents)} documents from '{folder}/'")
    print(f"Produced {len(chunks)} chunks "
          f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})\n")

    print("=== 5 sample chunks ===\n")
    for i, chunk in enumerate(chunks[:5], start=1):
        print(f"--- Sample {i} | source: {chunk['source']} "
              f"| length: {len(chunk['text'])} chars ---")
        print(chunk["text"])
        print()
