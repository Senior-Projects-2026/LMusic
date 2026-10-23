# LMusic: Constrained Lyric Generation

## 1. Problem Definition

Songwriters need lyrics that express emotion while respecting rhyme schemes, syllable counts, and rhythmic structure. General-purpose language models produce fluent text but do not reliably meet these constraints, leaving substantial manual revision. LMusic aims to support Romanian lyric writing through a resource-efficient assistant that generates, checks, and refines lyrics against explicit user requirements.

## 2. State of the Art

Existing approaches use constrained decoding, specialized rhyme/rhythm architectures, or generate-verify-refine loops. DeepRapper models rhyme and rhythm, while PoeTone and a Greek poetry verification pipeline demonstrate the value of external feedback. These approaches improve formal control but target other languages or require specialized generation methods. RAG provides context but does not itself guarantee valid rhyme or syllable counts. Our literature review and references are available in [sota.md](sota.md).

## 3. Proposal

**Fine-tuned SLM agent.** We will compare Phi-3-mini (3.8B), Llama-3.2-3B, and Qwen2.5-3B for Romanian quality, constraint adherence, and GPU requirements. The selected model will be adapted through QLoRA/PEFT, using Unsloth where compatible, on Google Colab or Kaggle. Training will target structured, emotion-conditioned lyric generation using legally usable and synthetic examples; synthetic rhyme and syllable targets will be filtered with our verification tools.

**RAG.** ChromaDB and Hugging Face embeddings will support retrieval over Top 100 Kiss FM / hit-song metadata and public-domain or compatibly licensed texts. Language, style, mood, and BPM metadata will guide retrieval. Retrieved context will inform themes and style without serving as lyrics to reproduce; commercial lyrics will not be redistributed without permission.

**MCP tools and refinement.** A Model Context Protocol server will expose `rhyme_checker` for end-word rhyme, `syllable_counter` for line-level syllable targets, and `sentiment_analyzer` for emotional fit. The agent will generate lyrics, call these tools, and revise flagged lines within a configurable iteration limit. It will report unresolved violations and uncertain analyses. Romanian phonetic ambiguities and sentiment-classification errors remain limitations; input/output moderation will also be included.

**Expected advantage.** Our contribution is the integration of Romanian-focused adaptation, retrieval, and reusable verification tools in a small-model pipeline. Compared with generation alone, this should improve constraint compliance and expose actionable feedback; compared with specialized architectures, it permits modular development without redesigning the model. These are hypotheses to test, not established superiority over SOTA.

**Evaluation.** A Golden Dataset of 40-50 prompts will cover Romanian-focused generation, analysis, grounded questions, and adversarial cases. We will compare the base model, fine-tuned model, fine-tuned model with RAG, and complete system. Measures include independently checked rhyme/syllable accuracy, retrieval context precision/recall and faithfulness, and human ratings of creativity, singability, emotional fit, and naturalness. Toxicity and unsupported claims will also be tracked.
