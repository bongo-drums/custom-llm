# Evidence card: test-1 (direct, one source)

| | |
|---|---|
| Mode | **ask** (standalone, no chat history, no persona) |
| Execution | **local**; internet reachable during run: **False** |
| Model | `gemma4:e2b`, 5.1B params, Q4_K_M, digest `7fbdbf8f5e45` |
| Runtime | Ollama 0.34.3 at http://localhost:11434 |
| Retrieval | bm25, top 6, 282 chars of evidence sent |
| Response time | 5.89 s total (load 0.03 s, prompt 559 tok, output 303 tok) |
| Loaded model memory | 1.71 GB (1.71 GB in VRAM) |
| Run at | 2026-09-29T18:05:41+00:00 |

## Question

> What is my golf handicap?

## Expected (written before the run)

**Answer:** About a 17.

- `raw/surfing-golf-and-running.md` › Golf: “My handicap is about a 17.”

## Retrieved passages (exactly what Gemma saw)

**[S1]** `raw/surfing-golf-and-running.md:5-7` · Golf · score 6.5622

```text
## Golf

I play golf about once a week, usually at Oakland Metro (Metropolitan Golf Links, next to the Oakland airport). My handicap is about a 17.
```

**[S2]** `raw/surfing-golf-and-running.md:1-3` · Surfing, Golf, Running and Everything Else · score 2.9281

```text
# Surfing, Golf, Running and Everything Else

_Written by me for this wiki, September 2026. First names only for people other than me._
```

## Gemma's answer

My handicap is about a 17 [S1].

## Automatic checks

- Expected passage retrieved: **True** (rank: {'Golf': 1})
- Mentions expected facts: {'17': True}
- Citation check: `status=cited  cited=S1`
- **Automatic verdict: PASS**

## Human assessment

PENDING: open each cited passage, judge support, and record the verdict in evals/assessments.json
