# Personal Wiki with Local Gemma + RAG

**Matt Wong · UC Berkeley Haas · Class 5, Assignment 4**

A command-line personal wiki about me: my resume, growing up in the Bay Area and playing football, and what I do outside work (surfing, golf, ultra running). A local Gemma model, run through Ollama, turns the originals into linked Obsidian notes. My own harness then gives the wiki three modes:

- **`chat`**: a personal assistant with memory of the conversation
- **`ask`**: grounded answers with citations, or an honest "insufficient evidence"
- **`search`**: the original passages, with no model involved

Everything runs offline once the model is downloaded.

> **Status of evidence.** The CLI, harness, retrieval and tests are built and pass (22 automated tests). The retrieval check has been run on the current sources: see [Evidence](#5-evidence). Two real `gemma4:e2b` ingest runs exist from an earlier version of the wiki built on my class-project READMEs (see [Development history](#development-history)). The **Gemma runs on the personal sources, the offline demo and the Obsidian screenshots are pending my laptop run**. Every table cell marked ⏳ is filled only from files the run writes to [`evidence/`](evidence/). No result in this README is invented.

**Quick links:**

- CLI and harness code: [`wiki_cli/`](wiki_cli/)
- Vault: [`vault/`](vault/) and [`vault/index.md`](vault/index.md)
- Instructions: [`instructions/`](instructions/)
- Test questions: [`evals/questions.json`](evals/questions.json)
- Evidence: [`evidence/`](evidence/)
- The plan I wrote before building: [`PLAN.md`](PLAN.md)

---

## 1. Purpose and sources

**What it's for:** a personal memory I can ask about my own life and career ("where do I surf?", "which of my employers was acquired?"), with every answer traceable to something I actually wrote.

| Original (unchanged, in `vault/raw/`) | What it is | Overview note |
|---|---|---|
| [`matt-wong-resume.md`](vault/raw/matt-wong-resume.md) | My resume (v08.07.26), exported from Word/PDF to Markdown. Phone number redacted; nothing else changed. | `wiki/Overview/Matt Wong Resume.md` |
| [`growing-up-and-football.md`](vault/raw/growing-up-and-football.md) | Written by me for this wiki: San Francisco, Hayward, Fremont Christian, Moreau Catholic football, College of San Mateo, transfer to Cal. | `wiki/Overview/Growing Up and Football.md` |
| [`surfing-golf-and-running.md`](vault/raw/surfing-golf-and-running.md) | Written by me for this wiki: golf at Oakland Metro, surfing Ocean Beach, the backyard ultra, running volume. | `wiki/Overview/Sports and Interests.md` |

Other people appear by first name only, because this repository is public. [`state/source_catalog.json`](state/source_catalog.json) maps each machine source ID to its original file, readable title, origin and SHA-256 hash (line-ending independent). `wiki status` re-checks the hashes, so anyone can confirm the originals are unchanged.

**How originals become pages:** `raw/<file>` → Gemma plans 3–5 topics → the harness sends Gemma only those sections → the harness writes the notes:

- `wiki/Overview/<Source>.md`: one per source, with key facts
- `wiki/Career/`, `wiki/Life/`, `wiki/Interests/`: one note per topic

Every fact bullet links to the exact original section, e.g. `[[ms-pacman-README#My hyperparameters|source]]`. Each note ends with a **Sources** list giving line ranges.

## 2. Setup and device

### Device ⏳ (filled from `wiki status` and the demo transcript's "Device" step)

| | |
|---|---|
| OS | ⏳ Windows 11 (version from transcript) |
| CPU | 13th Gen Intel Core i9-13900H (same laptop as Assignment 2) |
| GPU / dedicated VRAM | NVIDIA GeForce RTX 4060 Laptop GPU / 8 GB |
| Total RAM / available at run time | ⏳ |
| Free disk space | ⏳ |

### Model choice

- **Model:** Gemma, **E2B** size, `gemma4:e2b` from the Ollama library. The exact quantization and digest are recorded by `wiki status` ⏳. The official source is the [Gemma model page](https://ai.google.dev/gemma) and the Ollama library entry.
- **Runtime:** Ollama ⏳ version, serving `http://localhost:11434`.
- **Why E2B:** the course guidance for a PC with 6–8 GB of dedicated VRAM is "start with E2B, and try E4B only if the runtime and context fit".
  - E2B loads in about 2.9 GB at Q4_0. That leaves most of the 8 GB of VRAM for an 8K context window, Windows and other apps.
  - My wiki is small: 3 sources and about 42 passages. Ask mode sends at most about 6,000 characters (roughly 1,500 tokens) of evidence.
  - So I'm starting with the smallest model and upgrading only if it fails. Switching to E4B (`gemma4:e4b`, about 4.5 GB) is one line in `wiki.toml` or `--model gemma4:e4b`. If I switch, I keep the E2B results as evidence of what changed.
  - The 26B A4B MoE loads all 26B weights (about 14.4 GB), which doesn't fit in 8 GB of VRAM. It isn't a candidate.
- **Embeddings:** none by default. Retrieval is BM25 keyword search, so nothing extra has to be downloaded. The optional hybrid mode uses `embeddinggemma` through the same Ollama server.

### Measured memory and response time ⏳ (from [`evidence/SUMMARY.md`](evidence/SUMMARY.md))

| Measurement | Value | Source |
|---|---|---|
| Model loaded in memory (total / in VRAM) | ⏳ | `ollama ps` + `wiki status` (Ollama `/api/ps`) |
| Ingest of all 3 sources (wall time, model calls) | ⏳ | `evidence/ingest/ingest-*.json` |
| One ask answer (first call incl. load / warm) | ⏳ | `evidence/ask/test-*.json` → `timing` |
| Search (no model) | ~3 ms over 42 passages (build sandbox); 15–21 ms on the laptop with the earlier 70-passage wiki | `wiki search` header |

### Install (while online)

```powershell
# 1. Ollama (local model runtime): install from https://ollama.com/download, then:
ollama pull gemma4:e2b            # the model, about 3 GB; stored locally
ollama list                       # confirm it is listed
# optional, for hybrid retrieval only:  ollama pull embeddinggemma

# 2. This project: Python 3.11+, no third-party packages
cd personal-wiki
py -m venv .venv; .venv\Scripts\Activate.ps1     # macOS/Linux: python3 -m venv .venv && . .venv/bin/activate
pip install -e .                                  # installs the `wiki` command
wiki --help
```

`python -m wiki_cli <command>` works without installing. If `gemma4:e2b` isn't the tag your Ollama library shows, set `name` in [`wiki.toml`](wiki.toml) or pass `--model`.

### Commands

```powershell
wiki --help                                   # commands, configuration, required inputs
wiki status                                   # model/quantization/runtime, loaded memory, sources unchanged?, offline?
wiki ingest vault/raw                         # all sources -> vault/wiki + vault/index.md + retrieval index
wiki ingest vault/raw/surfing-golf-and-running.md   # one source again: updates its notes, no duplicates
wiki search "backyard ultra 50 miles"         # original passages + paths, no model (works with Ollama stopped)
wiki ask "What is my golf handicap?" --mode local
wiki chat                                     # assistant; /help /notes /sources /save /reset /exit
wiki eval --retrieval-only                    # step 1: did retrieval find the expected passages? (no model)
wiki eval                                     # step 2: the four ask-mode tests -> evidence/ask/test-*.md
python scripts/summarize_evidence.py          # collect measured numbers into evidence/SUMMARY.md
python -m unittest discover -s tests -v       # harness tests (no model needed)
```

**Errors are specific.** Each one tells you what to do next:

- Ollama not running → `Cannot reach the local model runtime … Start it with: ollama serve`
- Model missing → `Model 'gemma4:e2b' is not downloaded … run: ollama pull gemma4:e2b`
- Missing path → `No such file or folder`
- `--mode online` → says online mode isn't configured

## 3. Architecture

| Part | What it is here | Code |
|---|---|---|
| **Model** | Gemma E2B running in Ollama on my laptop. It sees only the messages the harness sends. It doesn't read files, remember sessions or call tools. | [`llm.py`](wiki_cli/llm.py) (HTTP to `localhost:11434`) |
| **Retrieval tool** | Splits sources into passages by Markdown heading and scores them with BM25. Returns passages with file, section and line range. | [`index.py`](wiki_cli/index.py) |
| **RAG workflow** | Ask mode: retrieve → assemble evidence + research rules → Gemma → citation check | [`harness.py`](wiki_cli/harness.py) `Harness.ask` |
| **Harness** | Everything that connects the parts: modes, instruction files, conversation history, routing (retrieve or not), prompt assembly, model calls, citation checks, errors, saved evidence | [`harness.py`](wiki_cli/harness.py), [`prompts.py`](wiki_cli/prompts.py), [`citations.py`](wiki_cli/citations.py), [`ingest.py`](wiki_cli/ingest.py), [`evals.py`](wiki_cli/evals.py) |
| **CLI** | The terminal interface: argument parsing, streaming output, exit codes | [`cli.py`](wiki_cli/cli.py) |

### One question traced end to end

`wiki ask "What is my golf handicap?"`

1. **`cli.main`** parses `ask` and loads `wiki.toml` into a `Config`. It builds a `Harness`, then calls **`cmd_ask`**. That rejects `--mode online`, prints the model/execution banner and calls `Harness.ask`.
2. **`Harness.ask`** loads [`instructions/wiki-instructions.md`](instructions/wiki-instructions.md), the research rules. It never loads `persona.md`, and it never sees chat history.
3. **Retrieval:** `Harness.retrieve(question, top_k=6, kinds=("raw",))` → `Index.search`.
   - The index is loaded from `.wiki_cache/index.json`. It is rebuilt automatically if any source changed.
   - The question is tokenized (lowercase, stopwords removed, light stemming) and every **original-source** passage gets a BM25 score. The top 6 come back with `file:start-end` and heading path.
4. **Context budget:** `prompts.select_passages` keeps passages in rank order up to 6,000 characters.
5. **Prompt:** `prompts.build_ask` numbers the passages `[S1]…[S6]`, each with its path, section and line range, then appends the question and the rule "cite [S#] or start with INSUFFICIENT EVIDENCE".
6. **Model call:** `OllamaClient.ensure_ready` confirms the model is pulled. `OllamaClient.chat` POSTs to `/api/chat` with `temperature 0.2`, `seed 42` and `num_ctx 8192`, and streams tokens to the terminal. Ollama's timing counts are kept.
7. **Citation check:** `citations.check` flags:
   - citations to passages that weren't shown
   - sentences with no citation
   - numbers that don't appear in the cited passage
   - sentences sharing few words with their cited passage

   It also detects `INSUFFICIENT EVIDENCE`.
8. **Display and save:** the CLI prints the answer, which passages were cited, the check result and timing. It saves the full record (question, passages, exact prompt, answer, checks, model identity, loaded memory, whether the internet was reachable) to `evidence/ask/`.

### How chat differs

`ChatSession.send` first **decides whether to retrieve** (`ChatSession.decide`):

- `/notes <query>` forces a lookup.
- Greetings and "what can you/we…" questions **skip** retrieval and get the capability list.
- Edits of the previous reply ("make that shorter", "turn it into bullets") **skip** retrieval and use the history.
- Anything else goes to a small schema-constrained Gemma call that returns `{needs_notes, search_query}`. The search query is rewritten to stand alone, so "where do I usually go?" after a surfing question still retrieves.

The prompt is `persona.md`, then the command list, then the last 6 exchanges, then the new message. Retrieved passages are attached **to that message only**. History stores the plain message and the reply, so an earlier reply can never be treated as verified evidence later.

`/save` writes the last reply to `drafts/`, which is outside the vault, never indexed and marked `not_evidence: true`. Saving is always an explicit user action.

### How search differs

`search` stops after step 3. It never contacts Ollama, which [a test proves](tests/test_wiki.py) by searching with the runtime unreachable. It searches originals only unless you add `--include-wiki`.

## 4. Design choices

**Passages.** Each passage is one Markdown section, split at blank lines into windows of about 1,200 characters. Image tags and link URLs are stripped for indexing, but line numbers always point at the unchanged original. Windows that are only a heading or only images are skipped. A heading's passage carries its own paragraph; for ingestion the harness sends the whole subtree (a `##` with its `###` children), since a parent heading often has one intro line and all the substance below it. The three sources become about 42 passages.

**Retrieval method.** BM25 is written in plain Python in `index.py`. It needs no download, it's easy to inspect, and it lets search run without the model. Section titles are counted twice, so a heading like "My hyperparameters" matters. Hybrid retrieval is available (`method = "hybrid"` in `wiki.toml`): BM25 plus EmbeddingGemma cosine, merged by reciprocal-rank fusion. It is for questions whose wording differs from the source.

**Which passages each mode may use.**

| Mode | Scope | Why |
|---|---|---|
| ask | originals in `raw/` only | Generated notes could carry an ingestion mistake. A test run showed generated summaries outranking the original passage that holds the answer. |
| search | originals only (add `--include-wiki` for notes) | Search is for inspecting the sources. |
| chat | originals + generated notes | Summaries help conversation, and chat's claims still need `[S#]`. |

**Research rules vs. personality.** They live in separate files that the harness loads per mode:

- [`wiki-instructions.md`](instructions/wiki-instructions.md), ask only: evidence only, cite every claim, neutral, `INSUFFICIENT EVIDENCE:` when unsupported
- [`persona.md`](instructions/persona.md), chat only: "Scout", a friendly, direct assistant. It lists what it really can and can't do, labels its own ideas "Suggestion:", and never invents personal facts.
- [`ingest-instructions.md`](instructions/ingest-instructions.md), ingest only

**Context limits.** `num_ctx = 8192` is set explicitly, because Ollama's default context is smaller.

| Step | What is sent |
|---|---|
| Ask | ≤ 6,000 characters of evidence plus about 400 tokens of rules |
| Chat | last 6 exchanges, plus ≤ 4 passages when it retrieves |
| Ingest planning | the source's outline: each section name plus its first 160 characters, never the whole file |
| Ingest note writing | ≤ 5,000 characters of the chosen sections |

**Structured ingestion.** Gemma plans topics and writes notes as JSON, using Ollama's schema-constrained output. The harness, not the model, decides filenames, folders, links and frontmatter. Before writing, it:

- **sanitizes titles:** 2–6 words; no hashes, dates, questions or sentences; no document scaffolding like "Education", "Screenshots" or "…Results"/"…Guide"; drops "My …" and dangling parentheticals
- **checks section names:** every section name Gemma returns must exist in the source outline
- **drops unsupported bullets:** any bullet with a number not found in its cited section, sharing under 25% of its words with it, ending mid-sentence, or consisting only of the heading, is dropped and logged in the ingest report
- **validates links:** each related-note link must point to an existing note, and a note from a different source is only a candidate if its title words appear in this page. Otherwise it is dropped, so a link can never break and the graph isn't padded.

**Naming and folders.** Notes are named for their subject (`Backyard Ultra.md`), and the H1 matches the filename.

- `wiki/Overview/`: one per source, titled from the catalog, not by the model
- `wiki/Career/`, `wiki/Life/`, `wiki/Interests/`

Machine IDs (`src-resume`) and original filenames live only in frontmatter and the catalog. `vault/index.md` is a human landing page, grouped by folder with one-line descriptions. Code, the retrieval index (`.wiki_cache/`), evidence, tests and drafts all live **outside** `vault/`. The Obsidian graph settings are committed ([`vault/.obsidian/graph.json`](vault/.obsidian/graph.json)): the filter is `path:wiki/`, attachments are hidden, and each folder has a color group.

**Re-ingestion without duplicates.** `state/pages.json` (created by the first ingest) records each page's content **per source ID**. Re-ingesting a source:

1. removes that source's previous contributions
2. matches new topic titles to existing ones, exactly or fuzzily (≥ 67% word overlap, so "Ocean Beach Surf Sessions" merges into "Ocean Beach Surfing")
3. rewrites the affected pages
4. retires any source whose file is gone from `raw/`, together with pages only it supported

It also tells Gemma which note titles already exist so it reuses them. Once I set `reviewed: true` on a corrected note, ingest never overwrites it. Tests cover all of this: re-ingesting yields the same file set, a hand-corrected reviewed note stays byte-identical, and removing a source removes its pages and leaves no broken link.

**Model settings.**

| Setting | Why |
|---|---|
| `temperature 0.2`, `seed 42` | answers and ingestion are repeatable |
| structured JSON calls at temperature 0 (0.4 on retry) | reliable schema output |
| `keep_alive 10m` | the model stays loaded between eval questions |

## 5. Evidence

| What | Where | Status |
|---|---|---|
| Plan and test questions written before building | [`PLAN.md`](PLAN.md), [`evals/questions.json`](evals/questions.json) | ✅ |
| Retrieval check: expected passage retrieved for tests 1–3 | [`evidence/retrieval/retrieval-check.md`](evidence/retrieval/retrieval-check.md) | ✅ build sandbox (deterministic; re-run offline ⏳) |
| Harness tests (22, incl. no-duplicate re-ingest, source retirement, ask ignores chat, chat skips lookup for capability questions) | [`tests/test_wiki.py`](tests/test_wiki.py) | ✅ `python -m unittest discover -s tests` |
| Ingestion runs on the earlier class-project sources (real `gemma4:e2b`, online) | [`evidence/ingest/`](evidence/ingest/) | ✅ two runs, see [Development history](#development-history) |
| Ingestion run on the personal sources | `evidence/ingest/` | ⏳ |
| Four ask-mode evidence cards | `evidence/ask/test-1.md` … `test-4.md` | ⏳ |
| Chat/search mode checks | `evidence/chat/*.md`, `evidence/search/`, `evidence/offline/transcript-*.txt` | ⏳ |
| Offline recording / transcript | `evidence/offline/` + screenshots | ⏳ |
| Obsidian screenshots: open note, index, graph (`path:wiki/`) | `evidence/obsidian/` | ⏳ |
| Measured numbers | [`evidence/SUMMARY.md`](evidence/SUMMARY.md) | ⏳ |

### Retrieval check (done, no model)

| Test | Question | Expected source › section | Rank in top 6 |
|---|---|---|---|
| 1 | What is my golf handicap? | surfing-golf-and-running › Golf | **1** |
| 2 | Which company I worked for got bought, who bought it, and for how much? *(paraphrase: the source says "acquired by Uber for $2.0Bn")* | resume › Postmates | **4** |
| 3 | Where did I go to community college, and what did I do there besides study? | resume › Education **and** growing-up › Football | **3** and **1** |
| 4 | Who was my head football coach at Moreau Catholic? | none should answer | Retrieves football passages; none names a coach. The true answer is recorded only in `evals/questions.json`, outside the vault. |

### Four ask-mode tests ⏳ (offline, local Gemma)

| Test | Retrieved expected? | Gemma's answer (short) | Citations check out? | Verdict |
|---|---|---|---|---|
| 1 | ⏳ | ⏳ | ⏳ | ⏳ |
| 2 | ⏳ | ⏳ | ⏳ | ⏳ |
| 3 | ⏳ | ⏳ | ⏳ | ⏳ |
| 4 (unsupported) | n/a | ⏳ | ⏳ | ⏳ |

For each card, I open every cited passage and record my verdict in `evals/assessments.json`, and the next `wiki eval` copies it into the cards. That file is keyed by test ID, e.g. `{"test-1": "Correct: 0.10 matches [S3] …"}`.

### Chat/search mode checks ⏳

Script: [`evals/chat_script.txt`](evals/chat_script.txt).

| Check | Expected |
|---|---|
| "what can we do?" and "what can you help me with?" | capabilities, `no notes lookup`, no refusal |
| draft a plan, then "make that shorter" | shorter version of *that* plan |
| "Where do I usually surf?" | notes retrieved, reply cites [S#] |
| chat claim "my coach was Andrew Cotter", then `wiki ask` the coach question in a fresh process | `INSUFFICIENT EVIDENCE` |
| `wiki search "backyard ultra 50 miles"` | passages and paths only |

### Obsidian ⏳

The screenshots go in `evidence/obsidian/`:

1. a topic note (e.g. `Backyard Ultra.md`) open, showing its source links and related notes
2. `index.md` or the file list
3. the graph with filter `path:wiki/` and attachments off

Then trace one note → a related note → a `[[growing-up-and-football#Football]]`-style link back into `raw/`.

## 6. Reflection

**Limitation 1, observed in the real ingest runs: a 2B model's topic choice isn't stable.** Ingesting the same three sources twice with `gemma4:e2b` (same seed, temperature 0) produced overlapping but different topic lists: the second run kept 7 of 11 pages, created 4 and removed 4. Two of the removed pages (`Integration Testing`, `Database Constraints`) were good. Since a re-ingest replaces a source's contributions with what the *current* run proposes, a good page can vanish when the model changes its mind.

- **Cause:** the plan prompt changed between runs (I edited the instructions), and small models are sensitive to that; but the design also has no memory of "topics that were good last time".
- **What already helps:** `reviewed: true` pins a page. Once I've checked a note, no ingest can remove or overwrite it.
- **Improvement to try:** show Gemma the existing topics *for this source* in the plan prompt and ask it to keep or explicitly drop each one with a reason, so removals are deliberate rather than accidental.

**Limitation 2, retrieval (no model involved).** For test 2 the resume's Postmates section ranks only **4th**: "company", "bought", "worked" match many resume sections, while the source says "acquired", not "bought". It's still inside the 6 passages Gemma sees, but with `top_k = 3` it would drop out. Hybrid retrieval (`method = "hybrid"`, EmbeddingGemma + BM25) is the fix to try.

**Gemma-side limitation on the personal wiki** ⏳: filled after the offline run, from what the cards actually show, whether it passes or fails.

## 7. Online mode

Not implemented. `--mode online` exits with a clear message. Every command in this README runs locally and offline.

## Development history

The wiki was first built on my three class-project READMEs (Assignments 1–3), because they were the only text of mine available in the cloud sandbox where the code was written. Two real `gemma4:e2b` ingest runs on those sources are kept as evidence:

| Run | What happened | Report |
|---|---|---|
| `ingest-20260926-213950` | First real run: 11 pages in 314 s, 19 model calls. Review against the originals found an empty page (`Training Results`), a note written from a parent heading's intro instead of its subsections (`Row Level Security`), and unrelated cross-project links. | [json](evidence/ingest/ingest-20260926-213950.json) |
| `ingest-20260926-215257` | Re-ingest after fixing the harness: 11 → 11 pages, no duplicates; 4 created, 4 removed, 7 updated; the two bad pages gone, three previously-lost topics recovered. | [json](evidence/ingest/ingest-20260926-215257.json) |

I then replaced the sources with personal ones, since a personal memory is what the assignment describes, and rewrote the four test questions. The harness code didn't change for the swap: only the category names, the persona's description of what the wiki contains, and the sources themselves.

## Repository layout

```
personal-wiki/
├── wiki_cli/            my CLI + harness (standard library only)
│   ├── cli.py           commands, output, errors
│   ├── harness.py       modes, routing, chat session, evidence records
│   ├── index.py         retrieval tool (sections -> passages -> BM25 / hybrid)
│   ├── prompts.py       prompt assembly per mode
│   ├── citations.py     automatic citation checks
│   ├── ingest.py        raw -> Gemma -> notes, titles, links, index.md, no-duplicate merge
│   ├── evals.py         four-test runner + retrieval-only check
│   ├── sources.py       source catalog, Markdown sections with line numbers
│   ├── llm.py           Ollama client (chat, JSON schema calls, embeddings, identity, memory)
│   └── config.py        wiki.toml loader
├── instructions/        persona.md (chat) · wiki-instructions.md (ask) · ingest-instructions.md
├── vault/               ← open THIS folder in Obsidian
│   ├── raw/             unchanged originals (resume, two notes I wrote)
│   ├── wiki/            generated, reviewed notes (Overview/ Career/ Life/ Interests/)
│   ├── attachments/
│   └── index.md
├── state/               source_catalog.json, pages.json (page registry for no-duplicate re-ingest)
├── evals/               questions.json (answer key, outside the vault) · chat_script.txt · assessments.json
├── evidence/            saved runs: retrieval/ ingest/ ask/ chat/ search/ offline/ obsidian/
├── scripts/             offline_demo.ps1 / .sh, summarize_evidence.py
├── tests/               unit + end-to-end tests (fake_ollama.py is a test double, never evidence)
├── wiki.toml            configuration
└── PLAN.md              gameplan written before building
```
