"""Retrieval + generation for The Unofficial Guide RAG pipeline.

Stages 4-5 of the architecture: embed the user's question, retrieve the top-5
most similar chunks from ChromaDB, and pass them as context to Groq's
llama-3.3-70b-versatile model, which answers ONLY from the retrieved reviews.
"""

# ChromaDB requires sqlite3 >= 3.35.0, but the system sqlite3 is older.
# Swap in the bundled pysqlite3 build before chromadb imports sqlite3.
__import__("pysqlite3")
import sys
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import os

import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

DB_PATH = "./chroma_db"
COLLECTION_NAME = "professor_reviews"
EMBED_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about CS professors at "
    "Florida State University, using only student reviews provided to you.\n"
    "Answer ONLY using the information in the provided documents. "
    "Do not use outside knowledge or make assumptions.\n"
    'If the answer is not contained in the documents, reply exactly: '
    '"I don\'t have enough information on that."'
)

load_dotenv()

# Load model, vector store, and Groq client once at import so repeated
# ask() calls (e.g. from a web UI) don't re-initialize them each time.
_model = SentenceTransformer(EMBED_MODEL)
_client = chromadb.PersistentClient(path=DB_PATH)
_collection = _client.get_collection(COLLECTION_NAME)
_groq = Groq(api_key=os.environ["GROQ_API_KEY"])


def ask(question):
    """Answer a question from the professor reviews.

    Returns a dict with:
      - answer:  the model's response, grounded only in retrieved chunks
      - sources: list of unique source filenames used as context
    """
    # Stage 4: embed the question and retrieve the top-k similar chunks.
    query_embedding = _model.encode(question).tolist()
    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
    )

    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    sources = list(dict.fromkeys(m["source"] for m in metadatas))

    # Build the context block, labeling each chunk with its source.
    context = "\n\n".join(
        f"[Source: {meta['source']}]\n{chunk}"
        for chunk, meta in zip(chunks, metadatas)
    )

    user_prompt = (
        f"Documents:\n{context}\n\n"
        f"Question: {question}"
    )

    # Stage 5: generate an answer grounded in the retrieved context.
    completion = _groq.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )
    answer = completion.choices[0].message.content

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    question = "What do students say about Professor Mills' teaching style?"
    result = ask(question)
    print(f"Q: {question}\n")
    print(f"A: {result['answer']}\n")
    print(f"Sources: {result['sources']}")
