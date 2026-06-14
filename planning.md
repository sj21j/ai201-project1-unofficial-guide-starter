# Project 1 Planning: The Unofficial Guide

<!-- > Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features. -->

<!-- --- -->

## Domain

Student reviews of CS professors at Florida State University. This knowledge is valuable because official course descriptions don't reflect grading style, exam difficulty, or workload. Rate My Professors aggregates honest peer experience that's hard to find officially.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 |RateMyProfessors |Sharanya Jayaraman |https://www.ratemyprofessors.com/professor/2290274 |
| 2 |RateMyProfessors |Robert Myers |https://www.ratemyprofessors.com/professor/113509 |
| 3 |RateMyProfessors |Zhenghao Zhang |https://www.ratemyprofessors.com/professor/1443006 |
| 4 |RateMyProfessors |Piyush Kumar |https://www.ratemyprofessors.com/professor/961670 |
| 5 |RateMyProfessors |David Whalley |https://www.ratemyprofessors.com/professor/1890966 |
| 6 |RateMyProfessors |Daniel Schwartz |https://www.ratemyprofessors.com/professor/2368226 |
| 7 |RateMyProfessors |Shifat Mithila |https://www.ratemyprofessors.com/professor/3036434 |
| 8 |RateMyProfessors |Christopher Mills |https://www.ratemyprofessors.com/professor/2599463 |
| 9 |RateMyProfessors |Shibo Li |https://www.ratemyprofessors.com/professor/3031542 |
| 10 |RateMyProfessors |Sonia Haiduc |https://www.ratemyprofessors.com/professor/2109201 |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
300 characters

**Overlap:**
50 characters

**Reasoning:**
Reviews are short paragraphs. 300 chars captures one complete thought without diluting meaning. Overlap ensures a sentence split across a boundary is still retrievable.
<!-- --- -->

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
all-MiniLM-L6-v2 via sentence-transformers

**Top-k:**
5

**Production tradeoff reflection:**
For production we'd weigh text-embedding-3-large (OpenAI) for better accuracy, but it has API cost and rate limits. all-MiniLM-L6-v2 runs locally for free with no latency penalty at this scale.
<!-- --- -->

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 |What do students say about Professor X's grading style? |curved/harsh/easy based on reviews |
| 2 |Does Professor Y give useful feedback on assignments? |yes/no + specifics |
| 3 |How difficult are exams in Professor Z's class? |hard/moderate + study tips |
| 4 |Would students recommend taking Professor A for Data Structures?|yes/no + reason |
| 5 |What do students say about Professor B's teaching style? |lecture-heavy, slides, etc. |

<!-- --- -->

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.Reviews use slang/nicknames, the embedding model may not match "Dr. J" to "Professor Johnson" well

2.Chunks may split mid-review, losing the context that makes a comment meaningful

<!-- --- -->

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->
Document Ingestion (raw .txt files)
        ↓
Chunking (Python, character split, size=300, overlap=50)
        ↓
Embedding (sentence-transformers / all-MiniLM-L6-v2)
        ↓
Vector Store (ChromaDB, local)
        ↓
Retrieval (top-5 semantic similarity)
        ↓
Generation (Groq / llama-3.3-70b-versatile)
        ↓
Gradio Web UI
<!-- --- -->

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
- **Tool:** Claude
- **Input:** My Documents and Chunking Strategy sections, plus the spec for two functions (`load_documents(folder)` and `chunk_documents(documents)`).
- **Expected output:** `ingest.py` where `load_documents` reads every `.txt` file into `{text, source}` dicts, and `chunk_documents` splits each into 300-char chunks with 50-char overlap, keeping `source` on every chunk.
- **Verification:** Print 5 sample chunks from the `documents` folder and confirm they read cleanly and that overlap carries text across chunk boundaries.

**Milestone 4 — Embedding and retrieval:**
- **Tool:** Claude
- **Input:** My Retrieval Approach section plus `ingest.py`, with the spec to embed all chunks and persist them in a local vector store.
- **Expected output:** `embed.py` that reuses `load_documents`/`chunk_documents`, embeds every chunk with `all-MiniLM-L6-v2` (sentence-transformers), and stores them in a persistent ChromaDB collection `professor_reviews` at `./chroma_db`, keeping the `source` filename as metadata. A retrieval function will then query the collection and return the top-5 most similar chunks.
- **Verification:** Print the total chunk count after indexing (expect 73), confirm `./chroma_db` persists between runs, and spot-check that a sample query returns relevant chunks with their source filenames.

**Milestone 5 — Generation and interface:**
- **Tool:** Claude
- **Input:** My Retrieval Approach and Architecture sections plus `embed.py`, with the spec for an `ask(question)` function and a web UI on top of it.
- **Expected output:** `query.py` with `ask(question)` that embeds the question with `all-MiniLM-L6-v2`, retrieves the top-5 chunks from the `professor_reviews` ChromaDB collection, and passes them as context to Groq's `llama-3.3-70b-versatile`, returning `{answer, sources}`. The system prompt forces answers to come only from the provided documents, replying "I don't have enough information on that." otherwise. The `GROQ_API_KEY` is loaded from `.env` via python-dotenv. A Gradio UI then wraps `ask()` for end users.
- **Verification:** Confirm an on-topic question returns a grounded answer with correct source filenames, and an off-topic question returns the "I don't have enough information on that." fallback.
