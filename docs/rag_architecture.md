# RAG Architecture & Chunking Strategy

## 1. Vector Database Selection: ChromaDB
We evaluated Qdrant and ChromaDB for our lyric-based RAG pipeline. We selected **ChromaDB** as our primary vector database for the following reasons:
*   **Team Expertise & Rapid Prototyping:** We have prior production experience with ChromaDB, allowing us to accelerate development and avoid unnecessary setup overhead.
*   **Seamless Python Integration:** ChromaDB runs natively in-memory or via local SQLite with a simple `pip install`, eliminating the need for Docker containers during the prototyping phase.
*   **Sufficient Metadata Filtering:** For our dataset scale (Top 100 hit songs), ChromaDB's built-in `where` clauses easily handle our required metadata filtering (e.g., `{"mood": "sad", "bpm": {"$lt": 100}}`) with near-zero latency.
## 2. Embedding Model: BGE-M3
Instead of the standard `all-MiniLM-L6-v2` (which is English-centric), we selected **BGE-M3** (`BAAI/bge-m3`):
*   **Multilingual Support:** It natively supports over 100 languages, making it highly effective for capturing semantic meaning in Romanian lyrics.
*   **Multi-Granularity:** It handles everything from short queries to long documents (up to 8192 tokens).
*   **Hybrid Retrieval:** BGE-M3 outputs dense, sparse, and multi-vector embeddings, which maps perfectly to Qdrant's hybrid search capabilities.

## 3. Music-Aware Chunking Strategy
Standard text chunking (e.g., splitting every 500 characters) destroys the rhythmic and structural integrity of a song. Our strategy is **Semantic Stanza Chunking**:
1.  **Split by Structural Markers:** The ingestion script will split text using double newlines (`\n\n`) and standard tags (`[Verse 1]`, `[Chorus]`, `[Bridge]`).
2.  **Preserve Rhyme Schemes:** A chunk will always contain a complete stanza (4 to 8 lines) so the SLM agent can analyze complete rhyme schemes (AABB, ABAB).
3.  **Metadata Injection:** Because a stanza out of context loses its song identity, every single chunk will have the song's global metadata appended to its payload (e.g., `Chunk: [Verse 1]... | Metadata: {artist: X, mood: Love, genre: Pop}`).