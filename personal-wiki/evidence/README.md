# Evidence

Every file here is written by a real run of the CLI. Nothing is typed in by hand, except my own verdicts in `../evals/assessments.json`.

| Folder | Written by | Contents |
|---|---|---|
| `retrieval/` | `wiki eval --retrieval-only` | Top-6 passages for each test question and the rank of the expected passage. No model is involved. |
| `ingest/` | `wiki ingest` | Pages created, updated and removed; every Gemma call with its timing; topics, bullets and links rejected by the harness's checks; model identity; whether the internet was reachable |
| `ask/` | `wiki eval`, `wiki ask` | `test-1..4.md` evidence cards plus full JSON (the exact prompt, passages, answer, citation check, timing, loaded memory) |
| `chat/` | `wiki chat` | Transcripts. Each turn records whether the harness looked up notes and why. |
| `search/` | `wiki search --save` | Raw search results |
| `offline/` | `scripts/offline_demo.ps1` / `.sh` | Full terminal transcript of the offline demonstration |
| `obsidian/` | me | Screenshots: open note, index or page list, graph (`path:wiki/`) |
| `SUMMARY.md` | `python scripts/summarize_evidence.py` | Measured numbers collected from the JSON files |

`retrieval/retrieval-check.md` was first produced in the cloud build sandbox, where Gemma could not be downloaded. BM25 is deterministic, so the offline laptop run should reproduce it exactly.
