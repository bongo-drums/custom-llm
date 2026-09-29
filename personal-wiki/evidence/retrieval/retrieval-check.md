# Retrieval check (no model)

Method: **bm25**, top 6 passages, over 49 indexed passages. Run with `wiki eval --retrieval-only`. This isolates the retrieval tool from Gemma.

## test-1: What is my golf handicap?

**PASS: expected passage(s) retrieved**. Expected ranks: `{'Golf': 1}`

| Rank | Location | Section | Score |
|---:|---|---|---:|
| 1 | `raw/surfing-golf-and-running.md:5-7` | Golf | 6.5622 |
| 2 | `raw/surfing-golf-and-running.md:1-3` | Surfing, Golf, Running and Everything Else | 2.9281 |

## test-2: Which company I worked for got bought, who bought it, and for how much?

**PASS: expected passage(s) retrieved**. Expected ranks: `{'Postmates': 4}`

| Rank | Location | Section | Score |
|---:|---|---|---:|
| 1 | `raw/matt-wong-resume.md:31-36` | Work Experience > SkyDeck — $85M Pre-Seed Fund investing in Berkeley's accelerator program (Berkeley, California) | 3.6402 |
| 2 | `raw/matt-wong-resume.md:38-46` | Work Experience > Gametime — Leading Ticketing Marketplace for last-minute offers across live events (San Francisco, California) | 2.8848 |
| 3 | `raw/matt-wong-resume.md:64-68` | Work Experience > Citigroup (San Francisco, California) | 2.3161 |
| 4 | `raw/matt-wong-resume.md:57-62` | Work Experience > Postmates — Food Delivery Marketplace acquired by Uber for $2.0Bn (San Francisco, California) | 1.684 |
| 5 | `raw/matt-wong-resume.md:24-29` | Work Experience > Corazon Capital — $330M Early-Stage Consumer Fund founded by the operators behind Match Group (Chicago, Illinois) | 1.5229 |
| 6 | `raw/matt-wong-resume.md:48-55` | Work Experience > Wonolo — Temporary Staffing Marketplace focused on front-line workers and laborers (San Francisco, California) | 1.4468 |

## test-3: Where did I go to community college, and what did I do there besides study?

**PASS: expected passage(s) retrieved**. Expected ranks: `{'Bachelor of Science || Education': 3, 'Football': 1}`

| Rank | Location | Section | Score |
|---:|---|---|---:|
| 1 | `raw/growing-up-and-football.md:15-19` | Football | 8.2208 |
| 2 | `raw/matt-wong-resume.md:70-74` | Additional | 1.9399 |
| 3 | `raw/matt-wong-resume.md:15-20` | Education > University of California, Berkeley – Haas School of Business (Berkeley, California) | 1.7278 |

## test-4: Who was my head football coach at Moreau Catholic?

**n/a: no passage should answer this; check that nothing retrieved states the answer**. Expected ranks: `{}`

| Rank | Location | Section | Score |
|---:|---|---|---:|
| 1 | `raw/growing-up-and-football.md:15-19` | Football | 5.3558 |
| 2 | `raw/growing-up-and-football.md:5-9` | Where I'm from | 4.1543 |
| 3 | `raw/matt-wong-resume.md:48-55` | Work Experience > Wonolo — Temporary Staffing Marketplace focused on front-line workers and laborers (San Francisco, California) | 3.4519 |
| 4 | `raw/growing-up-and-football.md:1-3` | Growing Up in the Bay Area and Football | 2.0801 |
| 5 | `raw/growing-up-and-football.md:21-23` | After football | 2.0682 |
| 6 | `raw/growing-up-and-football.md:11-13` | My parents | 1.6906 |
