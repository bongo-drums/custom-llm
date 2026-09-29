# Review log: generated notes checked against the originals

Every generated note was read next to its source after the first ingest of the personal sources
(`evidence/ingest/ingest-20260926-2*.json`, run 3). Corrections were made in the note, never in the
source, and each corrected note is marked `reviewed: true` so later ingests leave it alone.

| Note | What Gemma wrote | Original says | Fix |
|---|---|---|---|
| `Life/Football Career` | "started playing football in the sixth grade **at Moreau Catholic**" | Sixth grade came first; Moreau Catholic was high school (`growing-up-and-football.md` › Football) | Split into two sentences. Also moved from `Interests/` to `Life/` (it is school years, not a hobby). |
| `Overview/Matt Wong Resume` | "**earned** a Master of Business Administration … graduating in Spring 2027" | MBA in progress, graduation Spring 2027 (`matt-wong-resume.md` › Education) | "is pursuing" |
| `Overview/Matt Wong Resume` | "Sr. Finance & Strategy **Manager** at Postmates" | "Sr. Finance & Strategy **Analyst**" (› Postmates) | Corrected the title. An invented job title is exactly the kind of error the review step exists for. |
| `Career/Haas MBA Education` | "Honors: Cum Laude, Edgar J." | "Cum Laude, Edgar J. Kaiser Scholar" | Restored the truncated bullet. Cause was a harness bug (sentence trimmer treated "J." as a sentence end); fixed in code as well. |
| `Overview/*` summaries | "This project documents/summarizes …" | n/a (style) | Opener removed; the harness now strips "This project/overview …" too. |

Checked and found correct: `Golf Habits`, `Ocean Surfing`, `Weekly Running`, `Personal Life`, `Investment Banking Path`
(every number, place and name matches its cited section).

Harness finding from the same review: 13 of the 19 bullets dropped in this run were resume lines copied
word-for-word that end without a period, rejected as "fragments". They are now accepted when they appear
verbatim in the source. This cost the `Postmates Exit` and `Venture Fund Experience` topics; the next
ingest of the resume should recover them.

## Second review, after the offline run (2026-09-29)

The offline demonstration re-ingested all three sources (`ingest-20260929-175058`) and, as in every run, the
2B model chose a slightly different topic set: `Investment Banking Path` and `Venture Investing Experience`
were replaced by `Career Transition`, `Citigroup Role`, `Growing Up In Bay Area` and `High School Football`.
Reviewed notes were left alone, as designed. Reading the new pages against the originals:

| Note | What Gemma wrote | Original says | Fix |
|---|---|---|---|
| `Life/High School Football` | A second note on the same subject as the reviewed `Football Career`, again with "started playing football in the sixth grade **at Moreau Catholic**" | one subject, and sixth grade was before Moreau | **Merged**: page removed, its two incoming links redirected to `Football Career`. The title matcher (67% word overlap) did not catch "High School Football" vs "Football Career"; noted as a limitation. |
| `Life/Growing Up In Bay Area` | "played football from the sixth grade through senior year at Moreau Catholic" | same conflation, third time | Split into two clauses. |
| `Career/Citigroup Role` | summary was just "Citigroup Role" | n/a | Wrote a one-line summary from the Citigroup entry. The harness now falls back to the first detail when a summary is empty or echoes the title. |
| `Overview/Sports and Interests` | "This project documents …" | style | Opener removed; "documents" added to the harness's opener list. |
| `Career/Career Transition` | "are documented in this section" | "are in my resume" | Corrected. |

Checked and found correct: `Postmates Exit`, `Golf Habits`, `Ocean Surfing`, `Weekly Running`, `Personal Life`.
Every page is now `reviewed: true`, which freezes the wiki: later ingests can add pages but cannot change these.

**Pattern worth naming:** in three separate runs Gemma E2B merged "started playing football in the sixth grade"
and "at Moreau Catholic … through senior year" into one wrong sentence. The two facts sit one sentence apart in
the source. A larger model would likely not do this; for E2B the reviewed flag is the safeguard.

Also found: three reviewed notes (`Growing Up and Football`, `Matt Wong Resume`, `Haas MBA Education`) still linked to
`Investment Banking Path`, which the offline ingest had removed. Reviewed notes are never rewritten, so the links
dangled. Repointed them to `Career Transition` by hand; the harness now prints a warning when a run leaves a reviewed
note linking to a removed page.
