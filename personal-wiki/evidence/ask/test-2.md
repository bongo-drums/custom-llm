# Evidence card: test-2 (paraphrased (source says 'acquired by Uber for $2.0Bn' and 'S-1 publication and $2Bn sale'))

| | |
|---|---|
| Mode | **ask** (standalone, no chat history, no persona) |
| Execution | **local**; internet reachable during run: **False** |
| Model | `gemma4:e2b`, 5.1B params, Q4_K_M, digest `7fbdbf8f5e45` |
| Runtime | Ollama 0.34.3 at http://localhost:11434 |
| Retrieval | bm25, top 6, 3595 chars of evidence sent |
| Response time | 7.5 s total (load 0.01 s, prompt 1568 tok, output 438 tok) |
| Loaded model memory | 1.71 GB (1.71 GB in VRAM) |
| Run at | 2026-09-29T18:05:41+00:00 |

## Question

> Which company I worked for got bought, who bought it, and for how much?

## Expected (written before the run)

**Answer:** Postmates was acquired by Uber for $2.0Bn; Matt was the primary analyst on the fundraising and exit efforts.

- `raw/matt-wong-resume.md` › Postmates: “Postmates — Food Delivery Marketplace acquired by Uber for $2.0Bn ... Primary analyst on fundraising and exit efforts that led to a S-1 publication and $2Bn sale to Uber Technologies”

## Retrieved passages (exactly what Gemma saw)

**[S1]** `raw/matt-wong-resume.md:31-36` · Work Experience > SkyDeck — $85M Pre-Seed Fund investing in Berkeley's accelerator program (Berkeley, California) · score 3.6402

```text
### SkyDeck — $85M Pre-Seed Fund investing in Berkeley's accelerator program (Berkeley, California)
Pre-MBA Associate; Venture Fellow, June 2025 – Present

- Sourced three companies: two AI infrastructure (agent control, BaaS), one semiconductor (in-memory compute) startups
- Owned U.S university deal flow partner relationships resulting in 7 new university relationships
  - 1st intern to develop and lead roadshow in Boston – established partnerships at Boston University, MIT & Harvard
```

**[S2]** `raw/matt-wong-resume.md:38-46` · Work Experience > Gametime — Leading Ticketing Marketplace for last-minute offers across live events (San Francisco, California) · score 2.8848

```text
### Gametime — Leading Ticketing Marketplace for last-minute offers across live events (San Francisco, California)
Sr. Strategic Finance Manager, Direct Report to CFO, August 2023 – August 2025

- Managed Gametime's annual financial planning and goaling that led to the Company's first-ever profitable quarter
  - Partnered with VP-level executives to build, manage and track $100M+ budget across the organization
- Oversaw $80M+ marketing budget that has now resulted in $10M in incremental revenue from improving user economics
  - Revamped spend tracking to a data-driven approach for spend allocation resulting in 15% higher user conversion
- Established organization-wide testing program with $2 …
```

**[S3]** `raw/matt-wong-resume.md:64-68` · Work Experience > Citigroup (San Francisco, California) · score 2.3161

```text
### Citigroup (San Francisco, California)
Corporate Banking Analyst, May 2017 – November 2018

- Worked on capital raising, corporate strategy and capital allocation projects for 10+ clients (e.g Apple, Uber)
  - Uber's $1.13Bn Term Loan-B: Developed materials on Uber's financial and growth profiles for Citi's investment committee
```

**[S4]** `raw/matt-wong-resume.md:57-62` · Work Experience > Postmates — Food Delivery Marketplace acquired by Uber for $2.0Bn (San Francisco, California) · score 1.684

```text
### Postmates — Food Delivery Marketplace acquired by Uber for $2.0Bn (San Francisco, California)
Sr. Finance & Strategy Analyst, December 2018 – August 2020

- Primary analyst on fundraising and exit efforts that led to a S-1 publication and $2Bn sale to Uber Technologies
- Partnered with Growth Marketing on a $150M+ budget resulting in >5M new customer across >10 acquisition channels
- Oversaw Postmates' consolidated financial restructuring that resulted in 10% gross margin improvement over 2 years
```

**[S5]** `raw/matt-wong-resume.md:24-29` · Work Experience > Corazon Capital — $330M Early-Stage Consumer Fund founded by the operators behind Match Group (Chicago, Illinois) · score 1.5229

```text
### Corazon Capital — $330M Early-Stage Consumer Fund founded by the operators behind Match Group (Chicago, Illinois)
Summer Investment Associate, June 2026 – Present

- Sourced, diligenced and closed pre-seed investment (Upriver AI) – fastest sourced-to-close intern deal in firm history
- Led diligence on 8+ prospective deals across AI companions, consumer hardware and EdTech (Ollie AI, Freckle, Arrowster) – authored investment memos, market sizings and competitive landscapes for the partnership
- Built internal workflows (weekly relationship CRM), firm-wide newsletter and building deeper accelerator relationships
```

**[S6]** `raw/matt-wong-resume.md:48-55` · Work Experience > Wonolo — Temporary Staffing Marketplace focused on front-line workers and laborers (San Francisco, California) · score 1.4468

```text
### Wonolo — Temporary Staffing Marketplace focused on front-line workers and laborers (San Francisco, California)
Sr. Strategic Finance Manager, Direct Report to Head of Finance, September 2020 – May 2023

- Oversaw financial due diligence on two rounds of capital fundraising resulting in $160M+ raised
  - Restructured customer profitability analyses with a new cost methodology resulting in 20% profitability improvement
- Re-established improving user economics with Head of Marketing resulting in >100k new users with 30% greater profitability
- Led "Living Wage" initiative advocating sustainable income resulting in 25% worker wage increases within top 10 markets
- Managed $10M acquisition f …
```

## Gemma's answer

Postmates was acquired by Uber for $2.0Bn [S4].
This acquisition involved Postmates, a Food Delivery Marketplace [S4].
The transaction resulted in a $2.0Bn sale to Uber Technologies [S4].

## Automatic checks

- Expected passage retrieved: **True** (rank: {'Postmates': 4})
- Mentions expected facts: {'postmates': True, 'uber': True, '2': True}
- Citation check: `status=cited  cited=S4`
- **Automatic verdict: PASS**

## Human assessment

PENDING: open each cited passage, judge support, and record the verdict in evals/assessments.json
