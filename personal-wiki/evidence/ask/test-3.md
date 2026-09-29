# Evidence card: test-3 (connects two sources)

| | |
|---|---|
| Mode | **ask** (standalone, no chat history, no persona) |
| Execution | **local**; internet reachable during run: **False** |
| Model | `gemma4:e2b`, 5.1B params, Q4_K_M, digest `7fbdbf8f5e45` |
| Runtime | Ollama 0.34.3 at http://localhost:11434 |
| Retrieval | bm25, top 6, 1300 chars of evidence sent |
| Response time | 7.38 s total (load 0.01 s, prompt 846 tok, output 439 tok) |
| Loaded model memory | 1.71 GB (1.71 GB in VRAM) |
| Run at | 2026-09-29T18:05:41+00:00 |

## Question

> Where did I go to community college, and what did I do there besides study?

## Expected (written before the run)

**Answer:** College of San Mateo (2012-2014), where Matt was a student athlete with a 4.0 GPA; he went there wanting to keep playing football, then chose to focus on his studies and transferred to UC Berkeley.

- `raw/matt-wong-resume.md` › Bachelor of Science || Education: “Transferred from: College of San Mateo (2012-2014), San Mateo, California; Student Athlete, GPA 4.0”
- `raw/growing-up-and-football.md` › Football: “After high school I started at College of San Mateo, a community college, where I wanted to keep playing football.”

## Retrieved passages (exactly what Gemma saw)

**[S1]** `raw/growing-up-and-football.md:15-19` · Football · score 8.2208

```text
## Football

I started playing football in the sixth grade. At Moreau Catholic I played all the way through senior year, and I was team captain. My best friends from those years, Arthur and Tim, are still my best friends today.

After high school I started at College of San Mateo, a community college, where I wanted to keep playing football. I realized pretty quickly that I needed to focus on my studies instead, and I made the call to put school first. That paid off: I transferred to UC Berkeley to study business, with the goal of getting into finance.
```

**[S2]** `raw/matt-wong-resume.md:70-74` · Additional · score 1.9399

```text
## Additional

- Activities: Advisor, Kenta Ramen – Support family's restaurant (2012 – Present); Advisor, College of San Mateo – Keynote speaker for the Economics department (2023 – Present); Volunteer, MeWater Foundation – Surf volunteer (2024 – Present)
- Languages: Cantonese (fluent)
- Interests: Surfing (California, Hawaii), Ultra Running (50k+), Angel Investing (roots.home, etc.)
```

**[S3]** `raw/matt-wong-resume.md:15-20` · Education > University of California, Berkeley – Haas School of Business (Berkeley, California) · score 1.7278

```text
### University of California, Berkeley – Haas School of Business (Berkeley, California)
Bachelor of Science in Business Administration. Graduation Date: Fall 2016

- Honors: Cum Laude, Edgar J. Kaiser Scholar
- Internships: Citigroup, Dimensional Funds
- Transferred from: College of San Mateo (2012-2014), San Mateo, California; Student Athlete, GPA 4.0
```

## Gemma's answer

I attended the College of San Mateo, which is identified as a community college [S1]. Besides studying, the individual served as an Advisor for the Economics department [S2].

## Automatic checks

- Expected passage retrieved: **True** (rank: {'Bachelor of Science || Education': 3, 'Football': 1})
- Mentions expected facts: {'san mateo': True, 'football|athlete': False}
- Citation check: `status=cited  cited=S1,S2`
- **Automatic verdict: FAIL**

## Human assessment

PENDING: open each cited passage, judge support, and record the verdict in evals/assessments.json
