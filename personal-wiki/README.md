# Personal Wiki with Local Gemma + RAG

**Matt Wong · UC Berkeley Haas · Class 5, Assignment 4**

A command-line personal wiki about me: my resume, growing up in the Bay Area and playing football, and what I do outside work (surfing, golf, ultra running). A local Gemma model, run through Ollama, turns the originals into linked Obsidian notes. My own harness then gives the wiki three modes:

- **`chat`**: a personal assistant with memory of the conversation
- **`ask`**: grounded answers with citations, or an honest "insufficient evidence"
- **`search`**: the original passages, with no model involved

Everything runs offline once the model is downloaded.

> **Results in one paragraph.** Everything below ran on my laptop with Wi-Fi off on 29 September 2026 (`gemma4:e2b`, Q4_K_M, Ollama 0.34.3). Three of the four ask-mode tests passed with correct citations; test 3 is a documented failure (a cited, true, but wrong-period answer to a two-part question). The chat checks passed except one routing miss ("Where do I usually surf?" skipped the notes), which I fixed in the harness afterwards and re-ran offline; the re-run passed. Every number in this README comes from a file in [`evidence/`](evidence/); nothing is typed in from memory.

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

### Device (from the offline transcript's "Device" step and `wiki status`)

| | |
|---|---|
| OS | Windows 11 (NT 10.0.26200), PowerShell 5.1 |
| CPU | 13th Gen Intel Core i9-13900H |
| GPU / dedicated VRAM | NVIDIA GeForce RTX 4060 Laptop GPU, 8 GB (plus Intel Iris Xe integrated) |
| Total RAM | 31.7 GB |
| Free disk space | not measured; the model file is 7.16 GB and the project under 2 MB |

### Model choice

- **Model:** Gemma, **E2B** size, `gemma4:e2b` from the Ollama library (`ollama pull gemma4:e2b`). As reported by `wiki status`: family `gemma4`, 5.1B parameters (E2B's effective 2B plus its embedding tables), quantization **Q4_K_M**, GGUF file **7.16 GB**, digest `7fbdbf8f5e45`. The official source is Google's [Gemma model page](https://ai.google.dev/gemma); the weights came from the Ollama library.
- **Runtime:** Ollama **0.34.3**, serving `http://localhost:11434`.
- **Why E2B:** the course guidance for a PC with 6–8 GB of dedicated VRAM is "start with E2B, and try E4B only if the runtime and context fit".
  - E2B loads in about 2.9 GB at Q4_0. That leaves most of the 8 GB of VRAM for an 8K context window, Windows and other apps.
  - My wiki is small: 3 sources and about 42 passages. Ask mode sends at most about 6,000 characters (roughly 1,500 tokens) of evidence.
  - So I'm starting with the smallest model and upgrading only if it fails. Switching to E4B (`gemma4:e4b`, about 4.5 GB) is one line in `wiki.toml` or `--model gemma4:e4b`. If I switch, I keep the E2B results as evidence of what changed.
  - The 26B A4B MoE loads all 26B weights (about 14.4 GB), which doesn't fit in 8 GB of VRAM. It isn't a candidate.
- **Embeddings:** none by default. Retrieval is BM25 keyword search, so nothing extra has to be downloaded. The optional hybrid mode uses `embeddinggemma` through the same Ollama server.

### Measured memory and response time (from [`evidence/SUMMARY.md`](evidence/SUMMARY.md) and the offline transcript)

| Measurement | Value | Source |
|---|---|---|
| Model loaded in memory | **1.71 GB, all in VRAM**, 100% GPU, context 8192 (the 7.16 GB file is mostly embedding tables that Ollama does not keep resident) | `ollama ps`; Ollama `/api/ps` recorded in every evidence file |
| One ask answer, offline, model already loaded | **5.9–7.5 s** wall (load 0.01–0.03 s, prompt 559–1568 tokens, 303–439 output tokens) | `evidence/ask/test-*.json` → `timing` |
| Four ask tests end to end | 45.3 s | offline transcript, step 8 |
| Ingest of all 3 sources (23–24 model calls) | **301 s online** (26 Sep); **1,042 s and 1,223 s offline** (26 and 29 Sep) | `evidence/ingest/*.json` |
| Re-ingest of one source (8–9 calls) | 109 s online; 102 s and 870 s offline | same |
| Search (no model) | 0.2–0.3 s including Python start-up; the BM25 query itself is a few ms over 42 passages | transcript step 6, `wiki search` header |

The offline ingests were 3–4× slower than the online ones for the same sources and the same number of model calls. Per-call generation speed in the ask tests was normal (about 90 tokens/s), so the slowdown is in the long JSON-generating ingest calls. I don't know the cause; my best guess is a laptop power-saving profile while on battery with Wi-Fi off. I report it rather than hide it.

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

**Extra scripts:** `scripts/offline_demo.ps1` (the full offline run, logged to `evidence/offline/`), `scripts/offline_chat_check.ps1` (just the chat checks, used for the re-run after the router fix), `scripts/apply_assessments.py` (stamps my verdicts from `evals/assessments.json` into the cards without re-running the model), `scripts/summarize_evidence.py`.

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
- **Added after the offline run:** if the router says no but the message is a question about Matt himself ("I", "my", "me" + a question mark), the harness retrieves anyway. The 2B router had answered "no lookup" to "Where do I usually surf?". A wasted lookup costs a few hundred tokens; a missed one costs a wrong answer.

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
| Retrieval check: expected passage retrieved for tests 1–3 | [`evidence/retrieval/retrieval-check.md`](evidence/retrieval/retrieval-check.md) | ✅ re-run offline on the laptop (step 7 of the transcript), same ranks |
| Harness tests (22, incl. no-duplicate re-ingest, source retirement, ask ignores chat, chat skips lookup for capability questions) | [`tests/test_wiki.py`](tests/test_wiki.py) | ✅ `python -m unittest discover -s tests` |
| Ingestion runs on the earlier class-project sources (real `gemma4:e2b`, online) | [`evidence/ingest/`](evidence/ingest/) | ✅ two runs, see [Development history](#development-history) |
| Ingestion runs on the personal sources (online 26 Sep; offline 26 and 29 Sep) | [`evidence/ingest/`](evidence/ingest/) | ✅ |
| Review of generated notes against the originals, with every correction | [`evidence/review-log.md`](evidence/review-log.md) | ✅ |
| Four ask-mode evidence cards (offline, 29 Sep) | [`test-1`](evidence/ask/test-1.md) · [`test-2`](evidence/ask/test-2.md) · [`test-3`](evidence/ask/test-3.md) · [`test-4`](evidence/ask/test-4.md) | ✅ 3 pass, 1 fail |
| Chat mode checks (offline, 29 Sep) and the offline re-run after the router fix | [`chat-20260929-180635.md`](evidence/chat/chat-20260929-180635.md) (original, one failure), [`chat-20260929-183355.md`](evidence/chat/chat-20260929-183355.md) (re-run, all pass), [`chat-rerun log`](evidence/offline/chat-rerun-20260929-113344.txt) | ✅ |
| Search check (no model) | [`evidence/search/search-backyard-ultra-50-miles.json`](evidence/search/search-backyard-ultra-50-miles.json) | ✅ |
| Offline transcript and screenshot (Wi-Fi off in the taskbar) | [`evidence/offline/transcript-20260929-103013.txt`](evidence/offline/transcript-20260929-103013.txt), [`evidence/offline/wifi-off.png`](evidence/offline/wifi-off.png) | ✅ |
| Obsidian screenshots: open note, index, graph (`path:wiki/`, attachments off) | [`note`](evidence/obsidian/note-weekly-running.png) · [`index`](evidence/obsidian/index.png) · [`graph`](evidence/obsidian/graph.png) | ✅ |
| Measured numbers, collected from the JSON files | [`evidence/SUMMARY.md`](evidence/SUMMARY.md) | ✅ |

The PowerShell transcript records each command, its exit code and its duration; the CLI's own output for each step is in the JSON and Markdown files above (each carries `internet_reachable: false` and the model identity), and the terminal screenshot shows the last steps with the network icon crossed out.

### Retrieval check (done, no model)

| Test | Question | Expected source › section | Rank in top 6 |
|---|---|---|---|
| 1 | What is my golf handicap? | surfing-golf-and-running › Golf | **1** |
| 2 | Which company I worked for got bought, who bought it, and for how much? *(paraphrase: the source says "acquired by Uber for $2.0Bn")* | resume › Postmates | **4** |
| 3 | Where did I go to community college, and what did I do there besides study? | resume › Education **and** growing-up › Football | **3** and **1** |
| 4 | Who was my head football coach at Moreau Catholic? | none should answer | Retrieves football passages; none names a coach. The true answer is recorded only in `evals/questions.json`, outside the vault. |

### Four ask-mode tests (offline, `gemma4:e2b`, 29 Sep 2026)

| Test | Retrieved expected? | Gemma's answer (verbatim, shortened) | Do the cited passages support it? | Verdict |
|---|---|---|---|---|
| 1 golf handicap | yes, rank 1 | "My handicap is about a 17 [S1]." | Yes: [S1] is the Golf section, "My handicap is about a 17." | **PASS** |
| 2 acquired employer | yes, rank 4 | "Postmates was acquired by Uber for $2.0Bn [S4]. … a $2.0Bn sale to Uber Technologies [S4]." | Yes: [S4] is the Postmates entry; header and bullet both say it. | **PASS** |
| 3 community college | yes, ranks 1 and 3 | "I attended the College of San Mateo … [S1]. Besides studying, the individual served as an Advisor for the Economics department [S2]." | Half. [S1] supports the college. [S2] is a true resume line, but it is what I do at CSM *now* (keynote speaker since 2023), not what I did there as a student. The student-athlete/football facts were in [S1] and [S3], which Gemma had and didn't use. | **FAIL** |
| 4 head coach (unsupported) | n/a | "INSUFFICIENT EVIDENCE: The wiki does not contain information about the head football coach at Moreau Catholic." | No citation, no guess; the six retrieved passages don't name a coach. Same result in a fresh process right after telling the chat assistant the coach's name. | **PASS** |

My full verdicts are in [`evals/assessments.json`](evals/assessments.json) and at the bottom of each card. Test 3 is the important one: the automatic citation check passed it (every sentence cites a passage that really contains the claim), and only reading the passages shows the answer is to the wrong question. A citation is not proof.

### Chat/search mode checks (offline, 29 Sep; transcript: [`chat-20260929-180635.md`](evidence/chat/chat-20260929-180635.md))

Script: [`evals/chat_script.txt`](evals/chat_script.txt). Each turn's transcript line records whether the harness looked up notes and why.

| Check | Expected | Actual | Verdict |
|---|---|---|---|
| "what can we do?" / "what can you help me with?" | capabilities, no notes lookup, no refusal | Two bullet lists of real capabilities, `no notes lookup — question about the assistant's capabilities`, ends with a suggested starting point. | **PASS** |
| "Draft a short training plan for my first 100-miler next year." then "make that shorter" | a shorter version of *that* plan | Three-phase plan labelled "Suggestion:"; the follow-up returned the same three phases in one line each, `no notes lookup — follow-up edit of the previous reply`. | **PASS** |
| "Where do I usually surf?" | notes retrieved, reply cites [S#] | **First run:** router said `answerable from the conversation alone`; Scout replied "I don't have any information in Matt's wiki about where he usually surfs." The fact (Ocean Beach) is in the wiki. **Re-run offline after the harness fix** ([transcript](evidence/chat/chat-20260929-183355.md)): `harness rule: a question about Matt's own life always checks the notes` → "Matt usually surfs at Ocean Beach in San Francisco [S4]", citation check `cited`. | **FAIL → fixed, PASS on re-run** |
| chat claim "my football coach at Moreau was Andrew Cotter", then `wiki ask` the coach question in a fresh process | `INSUFFICIENT EVIDENCE` | Scout: "Got it. Thanks for letting me know about Andrew Cotter." Fresh `wiki ask`: `INSUFFICIENT EVIDENCE`, 6 passages shown, none cited. | **PASS** |
| `wiki search "backyard ultra 50 miles"` | passages and paths only, no model | Top passage `raw/surfing-golf-and-running.md:13-16` (Running), bm25, scope raw, no Ollama call. | **PASS** |

### Obsidian

Screenshots in [`evidence/obsidian/`](evidence/obsidian/): [`Weekly Running` open](evidence/obsidian/note-weekly-running.png) (filename = heading, four bullets each with a `source` link, related notes with reasons, Sources with line ranges), [the index](evidence/obsidian/index.png) grouped Overview / Career / Life / Interests, and [the graph](evidence/obsidian/graph.png) with filter `path:wiki/`, attachments off, colored by folder. Trace: `index` → `Weekly Running` → `Golf Habits` → its `source` link → `raw/surfing-golf-and-running.md` › Golf.

## 6. Reflection

**Limitation 1, observed in every ingest run: a 2B model's topic choice isn't stable.** Ingesting the same sources again with `gemma4:e2b` (same seed, temperature 0) produces overlapping but different topic lists every time: on the class-project sources the second run kept 7 of 11 pages; on the personal sources the offline run replaced `Investment Banking Path` and `Venture Investing Experience` with `Career Transition`, `Citigroup Role` and a duplicate `High School Football`. Since a re-ingest replaces a source's contributions with what the *current* run proposes, a good page can vanish when the model changes its mind, and a reviewed page can be left linking to a removed one (the harness now warns about that).

- **Cause:** the plan prompt changed between runs (I edited the instructions), and small models are sensitive to that; but the design also has no memory of "topics that were good last time".
- **What already helps:** `reviewed: true` pins a page. Once I've checked a note, no ingest can remove or overwrite it.
- **Improvement to try:** show Gemma the existing topics *for this source* in the plan prompt and ask it to keep or explicitly drop each one with a reason, so removals are deliberate rather than accidental.

**Limitation 2, retrieval (no model involved).** For test 2 the resume's Postmates section ranks only **4th**: "company", "bought", "worked" match many resume sections, while the source says "acquired", not "bought". It's still inside the 6 passages Gemma sees, but with `top_k = 3` it would drop out. Hybrid retrieval (`method = "hybrid"`, EmbeddingGemma + BM25) is the fix to try.

**Limitation 3, from the offline run: a cited answer to the wrong question (test 3).** Asked what I did at community college besides study, Gemma cited a true resume line about advising the college's Economics department, which is what I do there now, not as a student, while the football/student-athlete passage sat unused in its context. Every automatic check passed. Cause: a two-part question, a small model, and two passages that both mention "College of San Mateo". Improvement to try: ask Gemma to answer each part of a multi-part question separately with its own citation, and add a check that the cited passage's time period matches the question's ("did" vs "do"). I'd also add a second answerable two-source question so the eval has more than one data point on this.

**Limitation 4, from the offline run: the chat router.** The 2B router decided "Where do I usually surf?" needed no lookup. Fixed by a harness rule (a question about the user's own life always checks the notes) and re-run offline: the same script then answered from the notes with a citation. Both transcripts are kept. A smaller thing from the re-run: told the coach's name, Scout replied "I'll make a note that…", which it cannot do (saving is the user's explicit `/save`). Right behaviour, wrong wording; a persona line to tighten.

**Limitation 5, seen three times: the same conflated sentence.** In three separate ingests Gemma merged "started playing football in the sixth grade" and "at Moreau Catholic through senior year" into one wrong sentence, even though the source keeps them a sentence apart. Each time the review caught it; `reviewed: true` is what stops it coming back. Details in [`evidence/review-log.md`](evidence/review-log.md).

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
