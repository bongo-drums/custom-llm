# Evidence card: test-4 (unsupported: the answer is not in any source)

| | |
|---|---|
| Mode | **ask** (standalone, no chat history, no persona) |
| Execution | **local**; internet reachable during run: **False** |
| Model | `gemma4:e2b`, 5.1B params, Q4_K_M, digest `7fbdbf8f5e45` |
| Runtime | Ollama 0.34.3 at http://localhost:11434 |
| Retrieval | bm25, top 6, 2464 chars of evidence sent |
| Response time | 5.89 s total (load 0.01 s, prompt 1188 tok, output 303 tok) |
| Loaded model memory | 1.71 GB (1.71 GB in VRAM) |
| Run at | 2026-09-29T18:05:41+00:00 |

## Question

> Who was my head football coach at Moreau Catholic?

## Expected (written before the run)

**Answer:** INSUFFICIENT EVIDENCE. (True answer, kept out of the wiki on purpose: Coach Andrew Cotter.)

- No source should support an answer.

## Retrieved passages (exactly what Gemma saw)

**[S1]** `raw/growing-up-and-football.md:15-19` · Football · score 5.3558

```text
## Football

I started playing football in the sixth grade. At Moreau Catholic I played all the way through senior year, and I was team captain. My best friends from those years, Arthur and Tim, are still my best friends today.

After high school I started at College of San Mateo, a community college, where I wanted to keep playing football. I realized pretty quickly that I needed to focus on my studies instead, and I made the call to put school first. That paid off: I transferred to UC Berkeley to study business, with the goal of getting into finance.
```

**[S2]** `raw/growing-up-and-football.md:5-9` · Where I'm from · score 4.1543

```text
## Where I'm from

I was born in San Francisco, California. When I was four, my family moved to Hayward in the East Bay, and that's where I grew up. My family runs a restaurant, Kenta Ramen, and I've helped out there in one way or another since 2012.

I went to Fremont Christian through the eighth grade. For high school I moved to Moreau Catholic in Hayward.
```

**[S3]** `raw/matt-wong-resume.md:48-55` · Work Experience > Wonolo — Temporary Staffing Marketplace focused on front-line workers and laborers (San Francisco, California) · score 3.4519

```text
### Wonolo — Temporary Staffing Marketplace focused on front-line workers and laborers (San Francisco, California)
Sr. Strategic Finance Manager, Direct Report to Head of Finance, September 2020 – May 2023

- Oversaw financial due diligence on two rounds of capital fundraising resulting in $160M+ raised
  - Restructured customer profitability analyses with a new cost methodology resulting in 20% profitability improvement
- Re-established improving user economics with Head of Marketing resulting in >100k new users with 30% greater profitability
- Led "Living Wage" initiative advocating sustainable income resulting in 25% worker wage increases within top 10 markets
- Managed $10M acquisition f …
```

**[S4]** `raw/growing-up-and-football.md:1-3` · Growing Up in the Bay Area and Football · score 2.0801

```text
# Growing Up in the Bay Area and Football

_Written by me for this wiki, September 2026. Friends are first names only because this repository is public._
```

**[S5]** `raw/growing-up-and-football.md:21-23` · After football · score 2.0682

```text
## After football

I started my career in investment banking, then moved into startups because I wanted to make an impact I could actually see. The details of that path, from Citigroup to Postmates, Wonolo, Gametime and venture capital, are in my resume.
```

**[S6]** `raw/growing-up-and-football.md:11-13` · My parents · score 1.6906

```text
## My parents

My parents were always supportive of whatever activities I wanted to be part of. They never pushed me into Chinese school, piano lessons, or any of the things people stereotypically expect of an Asian American kid. If I wanted to play football, I played football. That freedom to choose is a big part of why I ended up doing the things I do now.
```

## Gemma's answer

INSUFFICIENT EVIDENCE: The wiki does not contain information about the head football coach at Moreau Catholic.

## Automatic checks

- Expected passage retrieved: **None** (rank: {})
- Mentions expected facts: {}
- Citation check: `status=insufficient`
- **Automatic verdict: PASS**

## Human assessment

PENDING: open each cited passage, judge support, and record the verdict in evals/assessments.json
