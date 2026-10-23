## 1. Problem Definition & Motivation

Songwriters and artists frequently experience creative blocks, particularly when attempting to marry raw emotional expression with **strict musical constraints**. Writing a successful song is not merely about generating creative text; it requires maintaining a consistent rhythmic meter, adhering to precise syllable counts per line, and executing structured rhyme schemes (such as AABB or ABAB) so that the lyrics naturally fit a vocal melody.

While standard, off-the-shelf Large Language Models (LLMs) like ChatGPT or Claude excel at generating fluent prose and free-form poetry, they *fundamentally fail* at professional songwriting. Because these models are **autoregressive**—predicting text token-by-token from left to right without phonetic look-ahead—they cannot reliably count syllables, anticipate stress patterns, or plan complex, valid rhymes. Furthermore, their outputs frequently rely on generic tropes and lack grounding in current musical trends. As a result, artists using standard LLMs are left with structurally flawed lyrics that require extensive human editing to become musically viable.

The **core goal** of this project is to solve these limitations by developing an intelligent, musically-aware assistant capable of generating *structured, emotionally resonant, and rhythmically valid* lyrics. By bridging the gap between open-ended semantic creativity and rigid mathematical constraints, we aim to provide a reliable tool that helps artists overcome writer's block, experiment with new styles, and accelerate their creative process without sacrificing technical quality.

## 3. Solution Proposal 

The proposed system combines a small language model (SLM), retrieval-augmented generation (RAG), and external verification tools in a generate-verify-refine pipeline for constrained lyric generation.

**Language model fine-tuning.** The initial implementation will compare Phi-3-mini (3.8B), Llama-3.2-3B, and Qwen2.5-3B, selecting the model based on Romanian language quality, constraint adherence, and available GPU memory. Parameter-efficient fine-tuning using QLoRA/PEFT, with Unsloth where compatible, will be used to adapt the selected model to songwriting tasks. The fine-tuning objectives include lyric structure, rhyme schemes (e.g., AABB and ABAB), syllable-aware line generation, and emotion-conditioned writing. Experiments will be conducted in a GPU notebook environment such as Google Colab or Kaggle. Fine-tuning examples will be drawn from legally usable or synthetic data. Synthetic examples will be filtered using the rhyme and syllable verification tools before training to reduce structurally incorrect training targets.

**Retrieval-augmented generation.** ChromaDB will provide the vector store for a curated corpus of legally usable Romanian and international song data. Hugging Face embedding models will support semantic retrieval, while metadata such as language, style, mood, BPM, and theme will enable context-aware selection. Where licensing permits, the corpus may include examples associated with Top 100 Kiss FM selections. Retrieved material will provide contextual and stylistic guidance rather than serve as text to reproduce.

**External verification tools.** An MCP (Model Context Protocol) server will expose three tools to support structural and emotional validation:

- `rhyme_checker` will assess end-word rhymes using phonetic representations and language-aware rules.
- `syllable_counter` will estimate syllable counts and identify line-level mismatches, with Romanian-specific handling where possible.
- `sentiment_analyzer` will estimate emotional tone and identify inconsistencies between generated lyrics and the requested mood.

The agent will generate candidate lyrics, call the MCP tools to check the requested constraints, and revise the lines flagged by verification. This loop will run for a configurable maximum number of iterations, after which the system will return the lyrics together with any unresolved constraint violations. Since phonetic and sentiment analysis may be imperfect, the system will report uncertainty when a constraint cannot be reliably verified. Input and output moderation, together with safeguards against unsafe or misleading retrieved content, will address relevant safety risks.

## Evaluation

Evaluation will use a **Golden Dataset of 30–50 challenging prompts** covering Romanian and English, different emotional requirements, rhyme schemes, syllable targets, and adversarial or unsafe inputs.

Four configurations will be compared under the same evaluation conditions: the base SLM, the fine-tuned SLM, the SLM with RAG, and the complete tool-verified system. Rhyme and syllable validity will be measured using independent checks. Retrieval quality and groundedness will be assessed using context precision, context recall, and faithfulness metrics inspired by RAGAS and the RAG Triad. Human evaluation will assess creativity, singability, emotional fit, and linguistic naturalness. Toxicity and unsupported claims will also be tracked.

The results will help determine whether fine-tuning, retrieval, and tool-based verification provide measurable improvements over the base model, rather than relying on fluency alone.

### Expected Contribution and Evaluation

Compared with general-purpose LLMs, which do not reliably enforce rhyme and syllable constraints, the proposed system combines fine-tuning, retrieval-augmented generation (RAG), and external verification tools to generate lyrics that better satisfy musical and emotional requirements. Unlike approaches based solely on constrained decoding or specialized architectures, this modular design integrates task-specific adaptation, context from a curated music corpus, and iterative verification without requiring a custom model architecture. These components aim to improve lyric validity, provide more transparent feedback, and remain practical with limited computational resources. The system will be evaluated against a baseline model using rhyme and syllable accuracy, emotional fit, and overall lyric quality, with particular attention to Romanian. Potential limitations, including copyright restrictions and inaccuracies in Romanian phonetic analysis, will also be considered. The evaluation will determine whether the proposed approach provides measurable improvements over the baseline.
