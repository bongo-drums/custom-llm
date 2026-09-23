# Gameplan: Personal Wiki with Local Gemma + RAG

I wrote this plan before building or testing anything. The README reports what actually happened. When the two differ, the README is right, and I note the change there.

## 1. The three choices

### Data: what the wiki is for

The wiki covers **my own Class 1–3 project write-ups**. It should answer questions like "what did I choose, why, and what happened?" for each project.

| Source (in `vault/raw/`) | Original location | What it covers |
|---|---|---|
| `networking-tracker-README.md` | `bongo-drums/networking-tracker` @ `a4ed1de` | Assignment 1: Next.js + Neon Postgres contact tracker with Row Level Security |
| `ms-pacman-README.md` | `bongo-drums/ms-pacman` @ `3993af6` | Assignment 2: DQN agent for Ms. Pac-Man, hyperparameters and results |
| `custom-llm-README.md` | `bongo-drums/custom-llm` @ `2cc9336` | Assignment 3: tiny nanoGPT trained from scratch on a CPU |

I wrote all three, so I have permission to publish them. They are copied byte-for-byte, and their SHA-256 hashes are in `state/source_catalog.json`.

### Model

- **Runtime:** Ollama. It serves a local HTTP API on `localhost:11434`, runs on Windows, macOS and Linux, and ships Q4 quantized Gemma builds.
- **Default model:** Gemma E2B (`gemma4:e2b`), the smallest size. My laptop from Assignment 2 is an i9-13900H with an RTX 4060 Laptop GPU (8 GB VRAM). The course guidance for 6–8 GB VRAM is "start with E2B, try E4B only if it fits". E4B is one config line away (`model = "gemma4:e4b"`).
- **Upgrade rule:** switch to E4B only if E2B fails the ingestion JSON or the grounded-answer tests. If I switch, I keep the E2B results as evidence.
- **Embeddings (optional):** `embeddinggemma` through the same Ollama server. Keyword retrieval never needs it.

### Retrieval

- **Default: BM25 keyword search**, written in plain Python, over passages split by Markdown heading. It needs no download and no model, so `wiki search` works with Ollama stopped.
- **Optional: hybrid.** BM25 plus local EmbeddingGemma vectors, merged with reciprocal-rank fusion. It is for paraphrased questions (Test 2). If it runs, I document the before/after.
- **Passages:** one Markdown section each, split into windows of about 1,200 characters at paragraph breaks. Each keeps its file, heading path and line numbers. Ask mode sends the top 6 passages (at most about 6,000 characters) to Gemma.

## 2. Four ask-mode tests (written before retrieval was built)

The tests live in `evals/questions.json`, outside the vault, so retrieval can't find the answer key.

| # | Question | Expected answer | Expected evidence |
|---|---|---|---|
| 1 | What exploration rate did I use when training the Ms. Pac-Man agent? | 0.10 (the notebook default was 0.20) | `ms-pacman-README.md` › My hyperparameters |
| 2 | How does my contacts app stop one user from seeing someone else's people? *(paraphrased: the source says "Row Level Security", "ownership", "policy")* | Postgres Row Level Security policies with `auth.user_id() = user_id`, enforced in the database rather than the UI | `networking-tracker-README.md` › Authentication and ownership |
| 3 | Which of my projects trained on a GPU and which trained only on a CPU? *(needs two sources)* | Ms. Pac-Man: RTX 4060 Laptop GPU with CUDA. Custom LLM: CPU only | `ms-pacman-README.md` › Results › Training budget + `custom-llm-README.md` › intro / run details |
| 4 | What grade did I receive on the Ms. Pac-Man assignment? | **Insufficient evidence.** No source mentions a grade. | none |

Mode checks (script: `evals/chat_script.txt`):

- Chat: "what can we do?" and "what can you help me with?" Expected: capabilities, no notes lookup, no refusal.
- Chat: "Draft a short study plan for reviewing my three projects", then "make that shorter". Expected: uses the conversation.
- Chat claim: "By the way, I got an A+ on the Pac-Man assignment." Then `wiki ask` the grade question in a fresh process. Expected: insufficient evidence, because chat is not evidence.
- Search: `wiki search "row level security policy"`. Expected: original passages and paths, no generated answer.

## 3. Architecture

```
wiki <command>                                  wiki_cli/cli.py      (argparse, errors, exit codes)
  ├─ ingest  → sources.py → ingest.py → llm.py → vault/wiki/*.md, vault/index.md, state/pages.json
  ├─ search  → index.py (BM25[/hybrid]) → print passages          (no model call)
  ├─ ask     → retrieve → prompts.build_ask() → llm.chat() → citations.check() → evidence/
  ├─ chat    → router (heuristic → Gemma classifier) → [retrieve] → prompts.build_chat() → llm.chat()
  ├─ eval    → runs evals/questions.json through ask → evidence cards
  └─ status  → runtime/model identity, quantization, loaded memory, network reachability
```

- **Model:** Gemma behind Ollama. It only sees the text the harness sends.
- **Retrieval tool:** `index.py`. It returns passages with paths, sections and line numbers.
- **RAG workflow:** the ask flow above.
- **Harness:** everything in `wiki_cli/`. It handles modes, instructions, history, routing, prompts, citation checks, errors and saved outputs.
- **Instructions live in files:**
  - `instructions/persona.md` for chat only
  - `instructions/wiki-instructions.md` for ask's research rules
  - `instructions/ingest-instructions.md` for page writing

## 4. Wiki design (for Obsidian and for retrieval)

- **Filenames:** short subject names like `Row Level Security.md`. The H1 matches the filename. A sanitizer rejects hashes, dates, full sentences and more than 6 words. Machine IDs go in frontmatter only.
- **Folders:** `wiki/Projects/` holds one note per source. `wiki/Concepts/` and `wiki/Tools/` hold topics.
- **Source references:** every detail bullet links to its raw section, e.g. `[[networking-tracker-README#Authentication and ownership]]`. Gemma may only pick section names the harness gave it. Invalid picks are repaired or dropped.
- **Links:** each page gets deterministic links (project ↔ topic) plus up to 3 Gemma-proposed related notes, each with a reason. Links to titles that don't exist are dropped, so no link can break.
- **No duplicates on re-ingest:** `state/pages.json` stores each page's contributions per source ID. Re-ingesting a source replaces its own contributions. It never adds a page with a near-duplicate title, because titles are fuzzy-matched against existing ones. Pages marked `reviewed: true` are never overwritten.
- **`vault/index.md`** is written by the harness and grouped by folder, with one-line descriptions. It also links the source catalog.
- **Kept outside the vault:** the machine files (retrieval index, logs, evidence, tests).

## 5. What must be run on my laptop (cannot be done in the cloud build sandbox)

The sandbox cannot download Gemma weights: Hugging Face, Ollama and Kaggle are blocked. So the code is built and unit-tested there with a fake model, and every real Gemma result comes from my laptop:

1. `ollama pull gemma4:e2b` (online).
2. Turn off Wi-Fi.
3. `scripts/offline_demo.ps1`. It runs status, ingest, search, the 4 ask tests, and the chat/ask mode checks, and records a transcript.
4. Review the generated pages against the originals, and fix any invented statements.
5. Take the Obsidian screenshots: an open note, the index or page list, and the graph filtered with `path:wiki/`.
6. Fill in the README's measured memory, timing and assessment sections from `evidence/`.
