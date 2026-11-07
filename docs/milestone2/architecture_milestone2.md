# LMusic Architecture Design & Project Plan

*Milestone 2*

## 1. Problem and data

### 1.1 Problem

General-purpose LLMs write fluent text but are unreliable at **Romanian rhyme and metre**. They generate token by token without "hearing" the words, so they miscount syllables and pair endings that do not rhyme. Most of their training data is English, which makes the problem worse for Romanian.

LMusic helps **songwriters who are stuck on a line or a chorus**, and **anyone curious** who wants better rhymes for a song, a poem or a toast. The user describes what they need, for example *"4 lines about a summer break-up, rhyme ABAB, 8 syllables per line, pop"*, and gets original lyrics that respect that form.

**Tasks**
1. **Constrained lyric generation** (main task): theme + form (lines, syllables, rhyme scheme) → original lyrics.
2. **Form analysis**: any text → its rhyme scheme and syllables per line.
3. **Trend guidance**: "what do current hits look like?" → genres, tempo and song structures from radio charts, used as style input for task 1.

### 1.2 Data

| Source | What we store | Why |
|---|---|---|
| Romanian **public-domain poems and songs** (e.g. Wikisource; folk songs; old songs) | Full text, split into stanzas | Correct Romanian rhyme and metre that we may legally store and show |
| **Lyrics written by the team**  | Full text | Modern song language; classic poems alone would make the output sound like the 19th century |
| **Synthetic lyrics**, kept only if they pass our syllable and rhyme checks | Full text | Scales the amount of modern-style examples |
| **Radio charts** (weekly Romanian airplay tops) | **Metadata only**: title, artist, rank, week, genre, tempo, structure | Shows which genres and styles are popular now, without copying protected lyrics |

**Copyright rule.** In Romania a work becomes free to use 70 years after its author's death, counted from 1 January of the following year (Law 8/1996). In 2026 that means authors who died in 1955 or earlier. For songs, what counts is the lyricist, not the performer. Current hits are protected, so we keep only their metadata.

### 1.3 Ingesting new data

New data is added with one command (or an upload in the UI). It is checked, split into stanzas, embedded and written to the database, and becomes searchable immediately, with no other change to the system.

```mermaid
flowchart LR
    A[New file] --> B[Check format<br/>and licence]
    B --> C[Split into stanzas<br/>+ metadata]
    C --> D[Embed]
    D --> E[(Qdrant)]
```

*How to read it:* a file is accepted only if its format is valid and its licence is allowed. Each stanza is then stored with its metadata.

Every stanza carries metadata that we can filter and audit on:

- `source`, `author`, `year` of the work, `license`
- `added_at`: when it entered the database, so the age of every record is visible
- `rhyme_scheme`, `n_lines`, `avg_syllables`: computed automatically by our tools
- `genre`, `emotion`, and `song_id` + `stanza_index`, to find the rest of the song

Re-importing the same file does not create duplicates: each stanza has a fixed id. Each week, the new radio top is added the same way.

---

## 2. RAG design

### 2.1 What retrieval is for: examples in the prompt (few-shot)

When a user asks for lyrics, the system first finds **2–3 real stanzas with a similar theme and the same form**, then gives them to the model **together with the request** as examples. A small model imitates a form it can see much better than a form described in words. The prompt tells it to use the examples for style and structure, never to copy them.

### 2.2 Chunking: one stanza per chunk, with metadata

- **Why stanzas.** Rhyme schemes and syllable patterns are defined per stanza, so every chunk has exactly one form and filters such as "ABAB, 4 lines, ~8 syllables" become exact. A stanza is also one idea (a verse or a chorus), and it is short (4–8 lines), which suits all embedding models.
- **Going back to the whole song.** Because each chunk stores `song_id` and `stanza_index`, a retrieved stanza can be "re-opened" into its full song when the context is needed.
- **What we will test.** Stanza chunks vs. whole-song chunks vs. single lines. We expect stanzas to work best, but we will decide by measurement.

### 2.3 Embedding models

We compare three open-source multilingual models of similar size (~0.6B parameters, 1024 dimensions). The scores are the MMTEB multilingual averages reported in the Qwen3-Embedding paper (same benchmark for all three):

| Model | MMTEB (multilingual) | Why consider it |
|---|---|---|
| Qwen3-Embedding-0.6B | **64.3** | Best score of the three |
| multilingual-e5-large-instruct | 63.2 | Strong, widely used baseline |
| BAAI/bge-m3 | 59.6 | Also produces word-level (sparse) vectors, useful for hybrid search |

A benchmark average does not show how a model handles Romanian lyrics, so we pick the model that retrieves best **on our own data** and on Romanian retrieval tasks (RoMTEB).

### 2.4 Vector database: Qdrant (vs. ChromaDB)

Both are open source and run **locally** from a folder on disk, with no server. We lean towards **Qdrant** because it supports **hybrid search**: one query combines meaning-based search (embeddings) with word-based search (BM25, with Romanian stemming). Lyrics need both: the right **theme** (meaning) and the right **sounds and words** (exact endings, refrains). We tested both: Qdrant ran hybrid search with metadata filters locally, while ChromaDB's local version does not support it (hybrid search is a Chroma Cloud feature).

### 2.5 RAG methods we will compare

**Method 1: standard RAG.** The request is used directly as the search query.

```mermaid
flowchart LR
    A[Request] --> B[Search Qdrant]
    B --> C[2-3 stanzas]
    C --> D[Request + examples<br/>to the model]
    D --> E[Lyrics]
```

*Why:* the simplest and fastest option; the baseline the others must beat.

**Method 2: HyDE (search with a statement, not a question).** The model first writes a rough stanza on the theme; that draft, not the request, is used to search.

```mermaid
flowchart LR
    A[Request] --> B[Model writes<br/>a rough stanza]
    B --> C[Search with<br/>the rough stanza]
    C --> D[2-3 stanzas]
    D --> E[Request + examples<br/>to the model]
    E --> F[Lyrics]
```

*Why:* a short request ("summer break-up") looks very different from a stanza, while a draft stanza looks like the stanzas we want to find (Gao et al., 2023). It costs one extra model call.

**Method 3: RAG with an LLM evaluator.** An LLM checks whether the retrieved stanzas really fit the request and whether the final answer does what was asked. Otherwise the system retries once or says it has nothing relevant (inspired by CRAG and Self-RAG).

```mermaid
flowchart LR
    A[Request] --> B[Search Qdrant]
    B --> C{Do the stanzas<br/>fit the request?}
    C -- no --> B2[Rewrite query,<br/>search again once]
    B2 --> D
    C -- yes --> D[Model writes lyrics]
    D --> E{Does it answer<br/>the request?}
    E -- yes --> F[Lyrics]
    E -- "no: retry once" --> D
```

*Why:* it stops irrelevant examples from steering the model and catches answers that miss the request, which reduces hallucination. It is the slowest method (up to two extra checks), so we measure whether the quality gain justifies the time.

**How we compare them.** On the Golden Dataset: whether the retrieved stanzas fit the request (context precision and recall), whether the lyrics respect the requested form, whether they copy any example, and response time.

---

## 3. Agent, Tools, and Model Choices

### 3.1 Model Choices (SLM)
For the core generative agent, we are targeting Small Language Models (SLMs) in the 3B-4B parameter range. This size is deliberately chosen to balance reasoning capabilities with hardware constraints, allowing us to perform QLoRA fine-tuning on consumer-grade GPUs (e.g., Google Colab, 16GB VRAM) and run fast, local inference for the iterative verify-refine loop.

Our primary candidates are:
*   **Phi-3-mini (3.8B):** Exceptional reasoning and instruction-following for its size; highly optimized for tool calling (crucial for our MCP setup).
*   **Llama-3.2-3B:** Meta’s latest lightweight model, offering robust context handling and strong base creativity.
*   **Qwen2.5-3B:** Included specifically for its superior native multilingual performance, which is a major advantage for processing Romanian lyrics and syntax.

**Rationale:** Rather than relying on massive, closed-source models via API (which introduce latency and cost), a locally fine-tuned SLM quantized to 4-bit (via `bitsandbytes`) guarantees data privacy, zero API costs, and the ability to strictly control the generation loop.

### 3.2 Agent and Tools (ReAct Loop via MCP)
The selected SLM will act as an orchestrator using a **ReAct (Reason + Act)** paradigm. Instead of predicting the perfect lyric in one shot, the Agent will generate a draft and independently decide to call verification tools.

These tools will be exposed systematically via a **Model Context Protocol (MCP) Server**:
1.  **`syllable_counter(line)`:** A deterministic Python function (using RoLEX or vowel-counting heuristics) that returns the exact syllable count of a generated string.
2.  **`rhyme_checker(word1, word2)`:** An algorithm verifying phonetic matching at the end of lines based on the user's requested scheme (AABB, ABAB).
3.  **`retrieve_lyrics(mood, genre)`:** The RAG interface allowing the agent to fetch inspirational context from our Vector DB when it lacks thematic direction.

**Decision Flow:** If the `syllable_counter` returns a mismatch (e.g., 9 syllables instead of the requested 8), the agent receives this error as context, discards the faulty line, and regenerates it. The agent is strictly constrained to a maximum of 3 refinement iterations to prevent infinite loops.

---

## 4. Golden Dataset & Evaluation Strategy

To rigorously evaluate both our RAG retrieval performance and the SLM's formal constraint adherence, we are constructing a versioned **Golden Dataset (`data/golden_dataset.json`)** comprising **30 to 50 diverse, complex songwriting prompts**.

### 4.1 Dataset Composition & Creation
The dataset is manually curated by the team to represent real-world artistic constraints and edge cases. Each entry in the JSON structure contains:
*   **User Prompt:** A realistic, multi-constraint request (e.g., *"Write a melancholic 4-line chorus about autumn in an ABAB rhyme scheme with exactly 8 syllables per line"*).
*   **Target Constraints:** Explicit metadata fields specifying the expected rhyme scheme, line count, syllable targets, and emotional tone.
*   **Ground-Truth Reference Context:** Representative source stanzas or metadata expected to be retrieved by the RAG pipeline.
*   **Expected Tool Invocations:** The anticipated sequence of checks (`syllable_counter` and `rhyme_checker`) and expected corrections during the ReAct loop.

### 4.2 Evaluation Metrics
We will evaluate our system against this dataset across three core dimensions:
1.  **Retrieval Evaluation (RAGAS / RAG Triad):** Measuring context precision and context recall to ensure Qdrant retrieves relevant stanzas that match the requested mood and form.
2.  **Constraint Adherence Score:** Using our automated MCP tools to independently verify whether the final generated lyrics strictly match the requested syllable count and rhyme scheme (aiming to significantly outperform the 0–4% baseline of raw LLMs).
3.  **Qualitative & Safety Metrics:** Human-in-the-loop evaluation for emotional resonance, singability, and naturalness, alongside automated checks for toxicity and hallucination mitigation.

---

## 5. Project Timeline (Weeks 6–14)
This timeline represents our commitment from the current architecture design phase to the final progress presentation.

*   **Week 6: Architecture & Evaluation Setup (Current)**
    *   Finalize and upload Architecture Document (Milestone 2).
    *   Complete `ingest_data.py` prototype and ChromaDB/Qdrant initialization.
    *   Publish `golden_dataset.json` (30-50 prompts).
*   **Week 7-8: Tooling & SLM Baseline**
    *   Develop and test the MCP Server with deterministic tools (syllables, rhymes).
    *   Set up the local/Colab training environment (Unsloth, HuggingFace).
    *   Run baseline evaluations (Zero-shot SLM vs. Golden Dataset).
*   **Week 9-10: Agent Integration & Fine-Tuning**
    *   Execute QLoRA fine-tuning on the chosen SLM using lyrical datasets.
    *   Integrate the RAG retrieval pipeline with the ReAct agent loop.
    *   Connect the Agent to the MCP server for the Generate-Verify-Refine loop.
*   **Week 11-12: Full System Evaluation & Pre-Christmas Milestone**
    *   Run comprehensive tests using RAG Triad (context precision, recall, faithfulness).
    *   Measure formal constraint adherence (rhyme/syllable accuracy post-refinement).
    *   Implement toxicity and moderation guardrails.
    *   *Deliverable:* Pre-Christmas GitHub Progress Review (Milestone 3).
*   **Week 13-14: Polish & Final Delivery**
    *   System optimization, bug fixing, and edge-case handling.
    *   Prepare CLI/UI interface for demonstrations.
    *   *Deliverable:* Final Progress Presentation (Week 14).

---

### References

Law 8/1996 on copyright (Romania) · Gao et al., *HyDE*, ACL 2023 · Yan et al., *Corrective RAG*, 2024 · Asai et al., *Self-RAG*, ICLR 2024 · Zhang et al., *Qwen3 Embedding*, 2025 · Chen et al., *BGE M3-Embedding*, 2024 · Wang et al., *Multilingual E5*, 2024 · RoMTEB (github.com/alina0195/roMTEB)
