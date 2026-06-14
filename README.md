# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

Student reviews of CS professors at Florida State University. This knowledge is valuable because official course descriptions don't reflect grading style, exam difficulty, or workload. Rate My Professors aggregates honest peer experience that's hard to find through official channels.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RateMyProfessors: Sharanya Jayaraman | Web reviews → `documents/prof_jayaraman.txt` | https://www.ratemyprofessors.com/professor/2290274 |
| 2 | RateMyProfessors: Robert Myers | Web reviews → `documents/prof_myers.txt` | https://www.ratemyprofessors.com/professor/113509 |
| 3 | RateMyProfessors: Zhenghao Zhang | Web reviews → `documents/prof_zhang.txt` | https://www.ratemyprofessors.com/professor/1443006 |
| 4 | RateMyProfessors: Piyush Kumar | Web reviews → `documents/prof_kumar.txt` | https://www.ratemyprofessors.com/professor/961670 |
| 5 | RateMyProfessors: David Whalley | Web reviews → `documents/prof_whalley.txt` | https://www.ratemyprofessors.com/professor/1890966 |
| 6 | RateMyProfessors: Daniel Schwartz | Web reviews → `documents/prof_schwartz.txt` | https://www.ratemyprofessors.com/professor/2368226 |
| 7 | RateMyProfessors: Shifat Mithila | Web reviews → `documents/prof_mithila.txt` | https://www.ratemyprofessors.com/professor/3036434 |
| 8 | RateMyProfessors: Christopher Mills | Web reviews → `documents/prof_mills.txt` | https://www.ratemyprofessors.com/professor/2599463 |
| 9 | RateMyProfessors: Shibo Li | Web reviews → `documents/prof_li.txt` | https://www.ratemyprofessors.com/professor/3031542 |
| 10 | RateMyProfessors: Sonia Haiduc | Web reviews → `documents/prof_haiduc.txt` | https://www.ratemyprofessors.com/professor/2109201 |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**
300 characters, using a fixed-size sliding window over each document's raw text (`chunk_documents()` in `ingest.py`).

**Overlap:**
50 characters. Consecutive chunks advance by 250 characters (size − overlap) so each chunk shares its first 50 characters with the end of the previous one.

**Why these choices fit your documents:**
The documents are Rate My Professors reviews: short, self-contained paragraphs rather than long-form guides. At 300 characters a chunk captures roughly one complete review or thought without diluting it with unrelated comments, which keeps embeddings focused and retrieval precise. The 50-character overlap means a sentence that lands on a chunk boundary still appears intact in the adjacent chunk, so a key phrase isn't lost to the split. Preprocessing is minimal: each `.txt` file is read as-is (one file per professor), blank/whitespace-only chunks are skipped, and the window stops once it reaches the end of the text so there are no trailing empty fragments. Each chunk keeps its `source` filename so attribution survives into the vector store.

**Final chunk count:**
73 chunks across 10 documents.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
`all-MiniLM-L6-v2` via `sentence-transformers`. Chunks are embedded in `embed.py` and the same model embeds the incoming question at query time in `query.py`, so both sides of the similarity search share one vector space. Vectors are stored in a persistent local ChromaDB collection (`professor_reviews` at `./chroma_db`). I chose it because it runs locally for free with no API cost or rate limits, is fast on CPU at this corpus size, and its 384-dimension embeddings are more than enough for short review text.

**Production tradeoff reflection:**
If I were deploying this for real users and cost weren't a constraint, I'd weigh a hosted model like OpenAI's `text-embedding-3-large` for higher accuracy on domain-specific and informal text, since student reviews are full of slang, nicknames ("Dr. J"), and course codes that a larger model is more likely to represent well. The tradeoffs: hosted models add per-request API cost, network latency, and rate limits, and create a dependency on an external service, whereas `all-MiniLM-L6-v2` runs in-process. `all-MiniLM-L6-v2` also has a short ~256-token input window, which is fine for 300-character chunks but would be limiting if I moved to longer documents; a model with a larger context window would let me use bigger chunks. Multilingual support isn't a concern here since the corpus is English-only.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
Grounding is enforced through both the system prompt and how the context is assembled. The exact system prompt sent to Groq's `llama-3.3-70b-versatile` (from `query.py`) is:

```
You are a helpful assistant answering questions about CS professors at Florida State University, using only student reviews provided to you.
Answer ONLY using the information in the provided documents. Do not use outside knowledge or make assumptions.
If the answer is not contained in the documents, reply exactly: "I don't have enough information on that."
```

Structurally, `ask()` retrieves the top-5 most similar chunks from ChromaDB and formats them into a labeled `Documents:` block, with each chunk prefixed by its `[Source: <filename>]`, followed by the user's question. Only those retrieved chunks are placed in the prompt, so the model has no other context to draw from. Generation runs at `temperature=0` for deterministic, faithful answers. Verified in practice: an off-topic question ("best pizza place in Tallahassee") returns the exact fallback line `I don't have enough information on that.` rather than an invented answer.

**How source attribution is surfaced in the response:**
`ask()` returns a dict `{answer, sources}`, where `sources` is the deduplicated list of source filenames behind the retrieved chunks (preserving retrieval order). The Gradio UI (`app.py`) displays the answer and the source filenames in separate textboxes, so the user always sees which professor review files an answer was drawn from.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Professor Zhang's grading style? | Generally lenient on grades: exams and the final are curved (one review notes a 90 was an A and an 85 an A-) and the grading scale is forgiving, but homeworks are graded harshly. Net: generous curving on tests, tough on homework. |According to the student reviews, Professor Zhang has a "very forgiving grading scale". The grading scale for the whole class is curved, with a 90 being an A and an 85 being an A-, indicating that he wants his students to make good grades. Additionally, it's mentioned that tests are easy and curved, which is a rare combination. Homework is also a significant portion of the grade, making up 40% of it. |Relevant |Accurate |
| 2 | Does Professor Kumar give useful feedback on assignments? | No. Multiple reviews say communication is scarce and to "not expect feedback on your assignments," with an outdated Canvas. Some students counter that he's knowledgeable, but on feedback specifically the consensus is negative. |According to one of the reviews, Professor Kumar does give useful feedback on assignments. |Relevant |Inaccurate |
| 3 | How difficult are exams in Professor Myers's class? | Hard. Tests are difficult and "insane if you're unprepared," and the first exam catches students off guard. Study tips: attend lectures (he explains concepts intuitively), know the concepts, and simulate as many multiple-choice questions as possible. |According to the student reviews, opinions on the difficulty of Professor Myers's exams vary. Some students found the tests to be "hard", "insane if you're unprepared", and that the first exam will "catch you completely off guard". However, another student stated that "Tests were not too hard" if you study and know the concepts. Overall, it seems that being prepared is key to doing well on his exams. |Relevant |Partially Accurate |
| 4 | Would students recommend taking Professor Whalley for Computer Organization/Architecture (CDA)? | No. Overwhelmingly not recommended. Lectures are described as just reading off slides, students feel they have to teach themselves, assignments are large with little time, and attendance is mandatory. Upside: grades were curved ~25% and he responds to emails and grades exams quickly. |No, students would not recommend taking Professor Whalley for Computer Organization/Architecture (CDA). They advise to "NEVER take Whalley" and suggest taking other CDA professors instead, as they have less material and easier exams. |Relevant |Accurate |
| 5 | What do students say about Professor Schwartz's teaching style? | Lecture-heavy slide reading: he reads off the slides/textbook and lectures are boring, but he's caring and responsive, gives lots of extra credit (attendance EC), and exams are fair and straightforward. |According to the provided documents, students say that Professor Schwartz's teaching style is boring, with lectures that involve a lot of information given while reading out of the textbook. One student also mentions that Schwartz doesn't do a great job teaching the material. |Relevant |Partially Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**
"Does Professor Kumar give useful feedback on assignments?" (Question 2 in the Evaluation Report, accuracy: Inaccurate.)

**What the system returned:**
"According to one of the reviews, Professor Kumar does give useful feedback on assignments."

This inverts the document consensus. The Kumar reviews lean negative on feedback specifically: one states plainly that the Canvas is outdated, "communication is scarce, and don't expect feedback on your assignments," while the positive reviews praise his intelligence and mastery of the subject, not his feedback. The correct grounded answer was "No."

**Root cause (tied to a specific pipeline stage):**
This is a two-stage failure spanning **retrieval (embedding)** and **generation**. First, `all-MiniLM-L6-v2` matches on semantic surface without polarity: the query "give useful feedback" embeds close both to the explicit negative chunk ("don't expect feedback on your assignments") and to positive but unrelated helpfulness chunks ("if you ask questions in lecture he won't hesitate to help"). The model can't tell from embedding distance that one of these *denies* feedback and the other is about a different kind of help, so the top-5 set is polarity-mixed. Second, at generation the model resolved that conflict the wrong way: its own phrasing, "According to one of the reviews," shows it generalized from a single minority chunk instead of weighing the balance of evidence. The grounding system prompt enforces "answer only from the documents" but says nothing about how to handle *conflicting* documents or report the majority view, so a faithfully-sourced single quote produced an answer opposite to the overall consensus.

**What you would change to fix it:**
At retrieval, increase `top_k` and/or add a re-ranking step so more of the negative-consensus chunks land in context, and consider hybrid keyword+semantic search so an explicit phrase like "don't expect feedback" isn't washed out by semantic neighbors. At generation, strengthen the system prompt to instruct the model to weigh the balance of reviews and explicitly note disagreement ("most students say X, though some say Y") rather than generalizing from one review. This failure is less about chunk boundaries than about polarity: for sentiment-heavy, conflicting review corpora, embedding similarity alone doesn't preserve whether a chunk affirms or denies the thing being asked about.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
Writing the Chunking Strategy and Retrieval Approach sections before any code meant each implementation step had concrete, agreed-upon numbers to build against rather than decisions made on the fly. When I built `ingest.py`, the 300-character / 50-overlap values came straight from the spec, so there was no guesswork about chunk size mid-implementation. The Architecture diagram also fixed the tool choices ahead of time (sentence-transformers → ChromaDB → Groq), so each module had a clear contract with the next, and I could build and verify the pipeline one stage at a time knowing how the pieces would connect.

**One way your implementation diverged from the spec, and why:**
The spec didn't anticipate an environment issue: ChromaDB requires sqlite3 ≥ 3.35.0, but the system's sqlite3 was 3.31.1, so the index wouldn't build as planned. I diverged by adding `pysqlite3-binary` and swapping it in at the top of every module that imports ChromaDB (`embed.py`, `query.py`) before chromadb loads, a detail the planning doc had no reason to foresee. A second, smaller divergence came at the interface stage: installing Gradio created a `huggingface-hub` version conflict with sentence-transformers, which I resolved by pinning `huggingface-hub<1.0`. Both changes were infrastructure fixes that kept the planned architecture intact rather than changes to the design itself.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* My Documents and Chunking Strategy sections from planning.md, plus a spec for two functions (`load_documents(folder)` and `chunk_documents(documents)`) with my stated 300-character / 50-overlap sizing, and a request to print 5 sample chunks so I could check readability.
- *What it produced:* `ingest.py` with a fixed-size sliding-window chunker (step = size − overlap), each chunk carrying its `source` filename, plus a sample-print block. Running it gave 10 documents → 73 chunks and printed samples that showed the overlap working across boundaries.
- *What I changed or overrode:* I directed it to verify the output by printing real chunks rather than trusting the code, which surfaced that fixed-character splitting cuts reviews mid-sentence, a limitation I then documented in the Failure Case Analysis instead of silently accepting it.

**Instance 2**

- *What I gave the AI:* My Retrieval Approach section and the existing `embed.py`, with a spec for `query.py`'s `ask(question)`: embed the question with `all-MiniLM-L6-v2`, retrieve the top-5 chunks from ChromaDB, pass them to Groq's `llama-3.3-70b-versatile`, return `{answer, sources}`, and enforce a system prompt that answers only from the documents.
- *What it produced:* `query.py` with the grounding system prompt, a labeled `[Source: …]` context block, `temperature=0`, and one-time loading of the model/DB/Groq clients at import. It then verified grounding by running an off-topic question, which correctly returned the "I don't have enough information on that." fallback.
- *What I changed or overrode:* When building the Gradio UI on top, the AI hit a real dependency conflict (Gradio bumping `huggingface-hub` past what sentence-transformers allows); I had it pin `huggingface-hub<1.0` and record the fix in requirements.txt rather than leave the environment broken. I also required that `app.py` never call `build_index` and instead rely on the pre-built `./chroma_db`.
