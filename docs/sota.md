# State of the Art: Constrained Lyric Generation with Agentic SLMs

**Project:** LMusic (VersAgent) | **Document:** RFC support, Week 4 | **Issue:** #3 | **Last updated:** 17 Oct 2026

> Scope: what the literature says about (1) generating lyrics/poetry under formal constraints, (2) retrieval and agent architectures, (3) parameter-efficient fine-tuning of small models, (4) evaluation, (5) safety, and (6) Romanian language resources. Each section ends with the **design decision** it supports in our project.

---

## 1. Summary (TL;DR)

1. **LLMs write fluent verse but do not reliably obey formal constraints** (rhyme, syllables, meter). Evidence is strongest in non-English and lower-resource languages.
2. **Deterministic verification inside a generate → verify → refine loop is the most effective fix reported so far.** A 2026 study on Greek poetry reports that pure LLM generation produced valid rhyme in only 0-4% of cases, versus 73.1% with a verification loop [8].
3. **Rule-based feedback can also be turned into training signal** (Generate-Critic fine-tuning for Chinese Songci [4]; DPO/KTO alignment from rule-based constraints for melody generation [9]). This supports our plan to filter synthetic fine-tuning data with our own linguistic tools.
4. **RAG, ReAct-style tool use, MCP, QLoRA and RAGAS-style evaluation are mature building blocks** with open implementations, so the originality of our project lies in how they are combined for Romanian lyrics, not in any single component.
5. **Gap:** within this survey we found no published system that combines a QLoRA-tuned SLM, an MCP server of Romanian phonological tools, RAG over annotated lyrics/poetry, and a formal-constraint evaluation suite for Romanian. The closest work targets Greek [8], Chinese [4], Arabic and Spanish.

---

## 2. Lyric and poetry generation under constraints

### 2.1 Why this is hard
Autoregressive language models predict tokens left to right without look-ahead, so they cannot easily plan that a line must end on a rhyming word or hit a syllable count [3]. A technical report on Chinese lyric generation likewise lists weak controllability (rhyme, line length) and topic drift after a few lines as open problems for large pre-trained models [2]. A recent JAIR survey covers poetry generation and evaluation from 2017 to 2025, including handling of meter, rhyme and stanza structure [13].

### 2.2 Families of approaches

| Family | Idea | Representative work | Relevance to us |
|---|---|---|---|
| Specialised decoding / sampling | Enforce syllables and rhyme during generation (forward + backward generation, constrained sampling, backtracking) | Weird AI Yankovic: parody lyrics with syllable and rhyme control [3]; constrained GPT-2 for Spanish poetry using backtracking to satisfy rhyme and meter [14] | Shows small models can obey constraints when decoding is controlled; hard to combine with hosted/quantised models |
| Architecture / training changes | Reverse-order generation, rhyme representations, rhyme constraints at inference | DeepRapper: rhyme and rhythm modelling for rap [5] | Inspiring for data formatting (e.g. rhyme-first tokens), heavy to reproduce |
| Constraint compilation + planning | Turn melody/rhythm into constraints, plan then write | LYRA: unsupervised melody-conditioned lyrics with outline stage and rhythm constraints; reports gains in singability, rhyme and quality [6] | Supports a *plan → write → verify* agent flow |
| Generate-Critic / verification loops | External rule-based checker gives feedback; model revises or is fine-tuned on the feedback | PoeTone (Songci): benchmarks 18 models, shows proprietary models lead, and that rule-based feedback fine-tuning improves formal conformity [4]; Greek hybrid "Prompt → LLM → Verify → Refine" pipeline [8] | **Closest match to our architecture** |
| Preference alignment from rules | Build preference pairs automatically from constraint violations, then DPO/KTO | Lyric-to-melody alignment with rule-based musical constraints [9] | Possible stretch goal after SFT |

### 2.3 Key quantitative evidence
- **Greek poetry (rhyme detection and generation):** pure LLM generation was reported at 0-4% valid rhyme; the generate-verify-refine loop reached 73.1% for the best model [8]. This is a single study on 26 test cases, so it should be treated as strong but small-scale evidence. The authors also stress that LLMs struggle most in lower-resource languages [8].
- **PoeTone:** even the best models face a trade-off between structural accuracy and poetic expressiveness, and rule-based feedback fine-tuning improved conformity for three open-source LLMs [4].
- **Self-Refine:** iterative self-feedback improved outputs by roughly 20% absolute on average across seven tasks without extra training [11]. Note that this is *self*-feedback; our loop will use *external deterministic* feedback, which the Greek and Songci results suggest is more reliable for formal constraints.

### 2.4 Design decisions for LMusic
- **D1.** Generation runs inside a **generate → verify → refine loop** with deterministic tools (`rhyme_checker`, `syllable_counter`, `meter_analyzer`) and a bounded number of iterations.
- **D2.** The metric we optimise and report is a **Formal Conformity Score** (rhyme-scheme match, syllable deviation, line count), modelled after PoeTone's evaluation protocol [4].
- **D3.** Ablation: *no loop* vs *loop* vs *loop + fine-tuned SLM*, mirroring the Greek study's with/without-verification design [8].
- **D4.** Stretch: build preference pairs from tool violations and test DPO/KTO [9].

---

## 3. Retrieval-Augmented Generation (RAG)

RAG combines a parametric model with a non-parametric index; the original formulation showed more specific, diverse and factual generation than a parametric-only baseline and provides provenance for answers [1]. For multilingual retrieval, **BGE-M3** supports dense, sparse and multi-vector retrieval in over 100 languages with inputs up to 8192 tokens, and its authors recommend a hybrid retrieval + re-ranking pipeline [7].

**Design decisions**
- **D5.** Embeddings: BGE-M3 as default, compared against at least one alternative multilingual embedder on our Golden Dataset.
- **D6.** Hybrid (dense + sparse) retrieval with a re-ranker and payload filters (emotion, BPM, genre) in Qdrant.
- **D7.** Chunking on **stanza** boundaries (natural semantic unit), with line-level and full-song variants as ablations.
- **D8.** RAG is a *tool the agent chooses to call*, not a fixed pre-step (see §4).

---

## 4. Agents, tool use and MCP

- **ReAct** interleaves reasoning traces with actions, which reduced hallucination and error propagation versus chain-of-thought on knowledge tasks and improved interpretability [10].
- **Model Context Protocol (MCP)** is an open protocol for connecting LLM applications to external tools and data. The specification has had several versions; the 2025-11-25 release is listed as the latest stable at the time of our search, adding structured features such as tasks and elicitation [12]. We should pin the spec/SDK version we use.

**Design decisions**
- **D9.** Agent loop in ReAct style over tool-calling; all linguistic and retrieval functions exposed as MCP tools so they are reusable and testable independently of the model.
- **D10.** Log every tool call (name, arguments, result) to make agent decisions auditable for the evaluation chapter.

---

## 5. Parameter-efficient fine-tuning and model choice

- **LoRA** freezes pre-trained weights and trains small low-rank matrices, cutting trainable parameters by orders of magnitude with no extra inference latency [15].
- **QLoRA** back-propagates through a frozen 4-bit quantised model into LoRA adapters; it reports preserving 16-bit fine-tuning quality while allowing very large models to be tuned on a single GPU, and notes that **small, high-quality datasets can suffice** [16]. This is what makes SLM fine-tuning feasible on Colab/Kaggle.
- **Candidate base models.** Qwen2.5 offers dense open models from 0.5B to 72B parameters and reports that small variants are suitable for resource-constrained settings [17]. **OpenLLM-Ro** provides open Romanian models (RoLlama, RoMistral, RoGemma families), instruction and alignment datasets, and Romanian evaluation sets, built partly from translated data whose errors the authors acknowledge can hurt quality [18][19].

**Design decisions**
- **D11.** Compare 3-4 candidate SLMs (e.g. a Qwen2.5 small model, a Gemma-based model, an OpenLLM-Ro model, and Phi-3-mini as required by the course brief) on a small Romanian formal-constraint benchmark *before* committing to fine-tuning. Model versions to be re-checked in Week 5 because the ecosystem moves quickly.
- **D12.** Fine-tune with QLoRA on three instruction types: constrained generation, analysis (emotion/rhyme scheme) and Q&A.
- **D13.** Build training data with a stronger model, then **filter it automatically with our own tools** (keep only examples that satisfy rhyme/syllable constraints), following the rule-based-critic idea in [4] and [9].

---

## 6. Evaluation

- **RAGAS** gives reference-free metrics for the retrieval, faithfulness and answer-quality dimensions of a RAG pipeline, without requiring human-labelled ground truth [20]. This maps directly to the RAG Triad required by the course (context precision/recall, faithfulness, relevance).
- **LLM-as-a-judge** can reach over 80% agreement with human preferences, matching human-human agreement, but suffers from position, verbosity and self-enhancement biases [21]. We therefore use it only for subjective quality, with randomised answer order, and never for rhyme or syllable correctness, which are computed deterministically.
- **PoeTone** is a useful template for multi-faceted poetry evaluation: formal conformity score, LLM-based quality assessment, human evaluation and probing tasks [4].

**Design decisions**
- **D14.** Golden Dataset of 40-50 prompts in four categories: constrained generation, analysis, factual Q&A grounded in the corpus, and adversarial/out-of-domain.
- **D15.** Three metric layers: (a) RAGAS RAG Triad, (b) deterministic formal metrics, (c) small human study (3-5 raters) on a sample for creativity/fluency, with LLM-judge calibrated against it.
- **D16.** Compare prompt versions (v1/v2/v3), RAG on/off, loop on/off, base vs fine-tuned vs commercial model, reporting the full table.

---

## 7. Safety: hallucination and toxicity

- A recent survey organises hallucination mitigation into prompt-based, retrieval-based, reasoning-based and model-centric (training/adaptation) techniques, and distinguishes factuality from faithfulness hallucinations [22][23]. Our system uses all four families in a light form: strict prompts, RAG grounding, tool verification, and fine-tuning.
- For toxicity, Llama Guard is an LLM-based input/output safeguard that natively covers only eight languages (Romanian is not among them) [24]. PL-Guard, a Polish safety benchmark, shows that gaps persist for medium-resource languages and that fine-tuned classifiers (e.g. a HerBERT-based one) are a viable remedy [24]. Multilingual Detoxify-style classifiers are commonly used for toxicity scoring across languages [25].

**Design decisions**
- **D17.** Two-stage guardrail: toxicity classifier on user input and on model output, plus a lyric-specific policy (hate, explicit violence/sexual content) enforced by rules.
- **D18.** Grounding policy: factual claims (artist, year, emotion tags) must cite a retrieved chunk; below a retrieval-score threshold the agent answers "no information". Faithfulness is checked with RAGAS-style claim verification [20].
- **D19.** Measure guardrail quality on ~20 adversarial prompts inside the Golden Dataset, and manually check false positives on legitimate dark/emotional lyrics, since toxicity filters can over-block art.

---

## 8. Romanian language resources

- **Syllabification and stress** are prerequisites for syllable counting and rhyme. Romanian has a base set of syllabification rules with several exceptions and a hiatus/diphthong ambiguity that complicates automatic syllabification [26]. The **RoLEX** dataset provides over 330,000 entries with syllabification, lexical stress and phonemic transcription, and was evaluated on predicting these properties [26]. Earlier work built a database of Romanian syllables [27] and studied Romanian rhyme detection from stressed vowels and syllabification [28].
- A 2024 study on rhythm in English and Romanian poetry stresses that rhythm depends on accurate syllabification and that algorithmic syllabification must handle many irregularities [29].
- **OpenLLM-Ro** provides Romanian LLMs and evaluation resources [18][19].

**Design decisions**
- **D20.** `syllable_counter` and `rhyme_checker` are built on RoLEX/Dexonline-style lexical data (syllables and stress) with rule-based fallback for out-of-vocabulary words; rhyme is computed from the last stressed vowel. **License and access of RoLEX and Dexonline data must be checked before use.**
- **D21.** Unit-test the tools on a hand-labelled set of Romanian verses (including diphthong/hiatus edge cases) and report their accuracy as a first-class result.

---

## 9. Copyright and data

Lyrics of commercial songs are copyright-protected. Our corpus plan:
1. Public-domain Romanian poetry (for example from Wikisource) and openly licensed text as the main retrievable corpus.
2. **Metadata and our own annotations only** (title, artist, emotion, BPM, genre, rhyme scheme) for commercial songs, without redistributing full lyrics.
3. Synthetic training data generated by us and validated by our tools.
4. A `plagiarism_check` tool to make sure generated lyrics do not reproduce existing text.

Research on memorisation and copying is an explicit evaluation axis in recent controlled-poetry work [30], which supports including this check in our evaluation.

---

## 10. Gap analysis and positioning

| Capability | Prior work (examples) | LMusic |
|---|---|---|
| Rhyme/meter control with LLMs | Chinese [4], Greek [8], Spanish [14], Arabic [30], English parody [3] | **Romanian** lyrics |
| Verification loop with deterministic tools | Greek pipeline [8], Songci critic [4] | Exposed as an **MCP server**, reusable by any agent |
| Fine-tuned small model | PEFT/LoRA is a standard route [15][16]; poetry-specific applications exist (to be surveyed further) | QLoRA SLM trained on **filtered, tool-verified** data |
| RAG over lyrics with emotion/BPM filters | Phrase-retrieval approaches [2] | Hybrid retrieval + payload filters + grounding policy |
| Evaluation | PoeTone multi-faceted protocol [4] | Formal metrics + RAG Triad + LLM-judge calibrated on humans, with ablations |

**Claimed contribution (to be validated by our experiments):** an open, reproducible, tool-augmented SLM pipeline for **Romanian** lyric generation with quantified gains from fine-tuning, the verification loop, and RAG.

**Limitations of this survey.** It is a time-boxed review for an RFC, not a systematic review. Some sources are arXiv preprints not yet peer reviewed, and we did not find (not "proved the absence of") Romanian-specific lyric generation work; we should repeat the search on Google Scholar and the ACL Anthology before the final report. Model and library versions must be re-checked at implementation time.

---

## 11. Bibliography

Links were retrieved during this research on 17 Oct 2026. Entries marked † are secondary pages or need a final check of venue details before submission.

**Lyric and poetry generation**
- [2] Report on Chinese lyric generation with a phrase retriever and phrase connector (arXiv 2303.11005; check exact title and authors on the arXiv page). https://arxiv.org/html/2303.11005v1 †
- [3] "Weird AI Yankovic: Generating Parody Lyrics" (arXiv 2009.12240). https://arxiv.org/pdf/2009.12240
- [4] "PoeTone: A Framework for Constrained Generation of Structured Chinese Songci with LLMs" (arXiv 2508.02515). https://arxiv.org/abs/2508.02515
- [5] "DeepRapper: Neural Rap Generation with Rhyme and Rhythm Modeling" (arXiv 2107.01875). https://arxiv.org/pdf/2107.01875
- [6] "Unsupervised Melody-Guided Lyrics Generation" (LYRA) (arXiv 2305.07760). https://arxiv.org/pdf/2305.07760
- [8] "LLMs Got Rhythm? Hybrid Phonological Filtering for Greek Poetry Rhyme Detection and Generation" (arXiv 2601.09631). https://arxiv.org/html/2601.09631v1
- [9] "Aligning Language Models for Lyric-to-Melody Generation with Rule-Based Musical Constraints" (arXiv 2604.18489). https://arxiv.org/pdf/2604.18489
- [13] "Computational Approaches to Automatic Poetry Generation and Evaluation: A Survey", JAIR. https://www.jair.org/index.php/jair/article/view/20584
- [14] "The tiny poet: artificial poetry generation with a constrained GPT-2 model", Procesamiento del Lenguaje Natural. http://journal.sepln.org/sepln/ojs/ojs/index.php/pln/article/download/6684/4075 †
- [30] "Shaer: Controlled Arabic Poetry Generation with Meter Subform and Semantic Conditioning" (arXiv preprint). https://arxiv.org/pdf/2610.09756 †

**RAG, agents, protocols**
- [1] Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", NeurIPS 2020 (arXiv 2005.11401). https://arxiv.org/abs/2005.11401
- [7] Chen et al., "BGE M3-Embedding" (arXiv 2402.03216). https://arxiv.org/abs/2402.03216
- [10] Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models", ICLR 2023 (arXiv 2210.03629). https://arxiv.org/abs/2210.03629
- [11] Madaan et al., "Self-Refine: Iterative Refinement with Self-Feedback" (arXiv 2303.17651). https://arxiv.org/abs/2303.17651
- [12] Model Context Protocol specification and version history. https://modelcontextprotocol.info/specification/ † (also see the official site, modelcontextprotocol.io)

**Fine-tuning and models**
- [15] Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models" (arXiv 2106.09685). https://arxiv.org/abs/2106.09685
- [16] Dettmers et al., "QLoRA: Efficient Finetuning of Quantized LLMs" (arXiv 2305.14314). https://arxiv.org/abs/2305.14314
- [17] Qwen Team, "Qwen2.5 Technical Report" (arXiv 2412.15115). https://arxiv.org/abs/2412.15115
- [18] "OpenLLM-Ro: Technical Report on Open-source Romanian LLMs" (arXiv 2405.07703). https://arxiv.org/abs/2405.07703
- [19] OpenLLM-Ro on Hugging Face. https://huggingface.co/OpenLLM-Ro

**Evaluation**
- [20] Es et al., "RAGAs: Automated Evaluation of Retrieval Augmented Generation", EACL 2024 demos (arXiv 2309.15217). https://arxiv.org/abs/2309.15217
- [21] Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", NeurIPS 2023 D&B (arXiv 2306.05685). https://arxiv.org/abs/2306.05685

**Safety**
- [22] Alansari and Luqman, "Large Language Models Hallucination: A Comprehensive Survey" (arXiv 2510.06265). https://arxiv.org/abs/2510.06265
- [23] Huang et al., "A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions" (arXiv 2311.05232). https://arxiv.org/html/2311.05232v2
- [24] "PL-Guard: Benchmarking Language Model Safety for Polish" (arXiv 2506.16322), which also reviews Llama Guard (Inan et al., 2023). https://arxiv.org/pdf/2506.16322
- [25] Detoxify multilingual toxicity classifier (usage documented in arXiv 2602.21236 †). https://arxiv.org/pdf/2602.21236

**Romanian resources**
- [26] Lőrincz et al., "RoLEX: The development of an extended Romanian lexical dataset and its evaluation at predicting concurrent lexical information". Natural Language Engineering, Cambridge University Press. https://www.cambridge.org/core/journals/natural-language-engineering/article/abs/rolex-the-development-of-an-extended-romanian-lexical-dataset-and-its-evaluation-at-predicting-concurrent-lexical-information/96A3933A2028BD8EE605E0E672A57EB2
- [27] Dinu and Dinu, "On the data base of Romanian syllables and some of its quantitative and cryptographic aspects", LREC 2006. https://aclanthology.org/L06-1179/
- [28] "On the Romanian rhyme detection", ACL Anthology C12-3011. COLING 2012. https://aclanthology.org/C12-3011.pdf (add authors from the PDF first page)
- [29] "Comparison of Rhythm in English and Romanian", International Journal of User-System Interaction 17(3), 2024. https://rochi.utcluj.ro/ijusi/articles/IJUSI-17-3-Motrun.pdf †
