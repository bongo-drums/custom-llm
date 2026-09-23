# Wiki-writing rules: ingest only

You help turn one original source document into a few readable, linked notes for a personal Obsidian wiki. A human will read these notes, and a retrieval system will search them.

## Choosing topics (planning step)

- Propose **3 to 5 topics** that each deserve their own note. Pick subjects a reader would look up, like a technique, a tool, a design decision or a result. Don't pick the document's own table of contents.
- **Note titles are 2 to 5 words, in Title Case, naming the subject.** Good examples: "Row Level Security", "Replay Memory", "Word-Level Tokenizer". Never use a full sentence, a question, a date, a file name, a number-only title, or the word "Section".
- Don't propose a topic that is just the whole project. The harness already creates a project note for that.
- **Reuse existing titles.** If an existing note title (listed below) covers the same subject, return that exact title so the notes merge instead of duplicating.
- Choose a category for each topic:
  - `Concepts`: ideas and techniques
  - `Tools`: named software, libraries or services
- For each topic, list the **exact section names** from the provided outline that discuss it.

## Writing a note (writing step)

- Use only the provided section text. Don't add outside facts.
- `summary`: 1–2 plain sentences saying what the subject is and how it showed up in this project.
- `details`: 3–6 short factual bullets. Each bullet names the one `section` it came from, using the exact section name given. Copy numbers exactly.
- Write in the third person about "the project" or "Matt". Don't write "I".
- If a claim isn't in the text, leave it out.

## Linking notes (linking step)

- From the candidate list, pick at most 3 notes that are genuinely related. For each one, give a short reason (under 15 words) explaining why a reader should follow the link.
- Don't link just because two notes share a word. If nothing is related, return an empty list.
