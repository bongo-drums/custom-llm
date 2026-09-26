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
