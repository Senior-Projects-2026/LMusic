## 1. Problem Definition & Motivation

Songwriters and artists frequently experience creative blocks, particularly when attempting to marry raw emotional expression with **strict musical constraints**. Writing a successful song is not merely about generating creative text; it requires maintaining a consistent rhythmic meter, adhering to precise syllable counts per line, and executing structured rhyme schemes (such as AABB or ABAB) so that the lyrics naturally fit a vocal melody.

While standard, off-the-shelf Large Language Models (LLMs) like ChatGPT or Claude excel at generating fluent prose and free-form poetry, they *fundamentally fail* at professional songwriting. Because these models are **autoregressive**—predicting text token-by-token from left to right without phonetic look-ahead—they cannot reliably count syllables, anticipate stress patterns, or plan complex, valid rhymes. Furthermore, their outputs frequently rely on generic tropes and lack grounding in current musical trends. As a result, artists using standard LLMs are left with structurally flawed lyrics that require extensive human editing to become musically viable.

The **core goal** of this project is to solve these limitations by developing an intelligent, musically-aware assistant capable of generating *structured, emotionally resonant, and rhythmically valid* lyrics. By bridging the gap between open-ended semantic creativity and rigid mathematical constraints, we aim to provide a reliable tool that helps artists overcome writer's block, experiment with new styles, and accelerate their creative process without sacrificing technical quality.

## 2. State of the Art

**Commercial tools.** Web-based generators (e.g. [Easy-Peasy.AI Rhyme Generator](https://easy-peasy.ai/templates/rhyme-generator)) and general chat LLMs (ChatGPT, Claude) produce fluent rhyming verse on any topic. *Pros:* easy to use, creative. *Cons:* closed systems with no published evaluation, no explicit verification of syllables or rhyme, no grounding in a music corpus, and unclear quality for Romanian.

**Academic approaches.**
- *Constrained decoding* (syllable- and rhyme-aware sampling, backtracking) makes even small models obey form [Weird AI Yankovic, 2020; Tiny Poet]. *Con:* hard to combine with modern quantized/hosted models.
- *Specialized architectures* such as DeepRapper (reverse-order generation with rhyme modelling) and LYRA (melody compiled into constraints) improve rhyme and singability. *Con:* expensive to train, task-specific.
- *Generate-Verify-Refine loops* with deterministic checkers are the most effective recent approach: a 2026 study on Greek poetry reports 0–4% valid rhymes from LLMs alone versus 73.1% with a verification loop; PoeTone (Chinese Songci) shows rule-based feedback can also be used to fine-tune open models. *Con:* demonstrated mainly for Chinese, Greek, Arabic and Spanish, not Romanian.

**Building blocks** are mature and open: RAG with multilingual hybrid retrieval (BGE-M3), ReAct-style tool use, MCP, QLoRA fine-tuning of small models, and RAGAS evaluation. Romanian resources exist for syllabification and stress (RoLEX) and for open Romanian LLMs (OpenLLM-Ro).

**Gap.** We found no system combining a fine-tuned SLM, verification tools for Romanian phonology exposed via MCP, RAG over annotated lyrics, and a formal-constraint evaluation. Full review and references: [`extended_research.md`](extended_research.md).

## 3. Proposal

**Fine-tuned SLM agent.** We will compare Phi-3-mini (3.8B), Llama-3.2-3B, and Qwen2.5-3B for Romanian quality, constraint adherence, and GPU requirements. The selected model will be adapted through QLoRA/PEFT, using Unsloth where compatible, on Google Colab or Kaggle. Training will target structured, emotion-conditioned lyric generation using legally usable and synthetic examples; synthetic rhyme and syllable targets will be filtered with our verification tools.

**RAG.** ChromaDB and Hugging Face embeddings will support retrieval over Top 100 Kiss FM / hit-song metadata and public-domain or compatibly licensed texts. Language, style, mood, and BPM metadata will guide retrieval. Retrieved context will inform themes and style without serving as lyrics to reproduce; commercial lyrics will not be redistributed without permission.

**MCP tools and refinement.** A Model Context Protocol server will expose `rhyme_checker` for end-word rhyme, `syllable_counter` for line-level syllable targets, and `sentiment_analyzer` for emotional fit. The agent will generate lyrics, call these tools, and revise flagged lines within a configurable iteration limit. It will report unresolved violations and uncertain analyses. Romanian phonetic ambiguities and sentiment-classification errors remain limitations; input/output moderation will also be included.

**Expected advantage.** Our contribution is the integration of Romanian-focused adaptation, retrieval, and reusable verification tools in a small-model pipeline. Compared with generation alone, this should improve constraint compliance and expose actionable feedback; compared with specialized architectures, it permits modular development without redesigning the model. These are hypotheses to test, not established superiority over SOTA.

**Evaluation.** A Golden Dataset of 40-50 prompts will cover Romanian-focused generation, analysis, grounded questions, and adversarial cases. We will compare the base model, fine-tuned model, fine-tuned model with RAG, and complete system. Measures include independently checked rhyme/syllable accuracy, retrieval context precision/recall and faithfulness, and human ratings of creativity, singability, emotional fit, and naturalness. Toxicity and unsupported claims will also be tracked.
