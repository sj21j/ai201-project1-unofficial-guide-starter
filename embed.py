"""Embedding and vector store for The Unofficial Guide RAG pipeline.

Stage 3 of the architecture: embed every chunk with sentence-transformers
(all-MiniLM-L6-v2) and store the vectors in a persistent local ChromaDB
collection named `professor_reviews`, keeping the source filename as metadata.
"""

# ChromaDB requires sqlite3 >= 3.35.0, but the system sqlite3 is older.
# Swap in the bundled pysqlite3 build before chromadb imports sqlite3.
__import__("pysqlite3")
import sys
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import load_documents, chunk_documents

DOCS_FOLDER = "documents"
DB_PATH = "./chroma_db"
COLLECTION_NAME = "professor_reviews"
EMBED_MODEL = "all-MiniLM-L6-v2"


def build_index():
    """Load chunks, embed them, and store them in a persistent ChromaDB collection."""
    documents = load_documents(DOCS_FOLDER)
    chunks = chunk_documents(documents)
    print(f"Loaded {len(documents)} documents -> {len(chunks)} chunks")

    print(f"Loading embedding model '{EMBED_MODEL}'...")
    model = SentenceTransformer(EMBED_MODEL)

    texts = [c["text"] for c in chunks]
    print("Embedding chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    # Persistent client so the index survives between runs.
    client = chromadb.PersistentClient(path=DB_PATH)
    # Start from a clean collection so re-runs don't duplicate chunks.
    client.delete_collection(COLLECTION_NAME) if COLLECTION_NAME in [
        c.name for c in client.list_collections()
    ] else None
    collection = client.create_collection(COLLECTION_NAME)

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": c["source"]} for c in chunks]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Stored {collection.count()} chunks in collection "
          f"'{COLLECTION_NAME}' at {DB_PATH}")


if __name__ == "__main__":
    build_index()
