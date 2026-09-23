"""Prompt assembly. The model only knows what these functions put in front of it.

Each mode loads its own instruction file:
  ask    -> instructions/wiki-instructions.md  (research rules, no persona, no history)
  chat   -> instructions/persona.md            (+ capabilities, + history, + optional passages)
  ingest -> instructions/ingest-instructions.md
"""

from __future__ import annotations

from pathlib import Path

from .index import Passage


def load_instruction(instructions_dir: Path, name: str) -> str:
    path = instructions_dir / name
    if not path.exists():
        raise FileNotFoundError(f"Missing instruction file: {path}. The harness needs it to build the {name} prompt.")
    return path.read_text(encoding="utf-8").strip()


def select_passages(passages: list[Passage], max_chars: int) -> list[Passage]:
    """Keep passages in rank order until the character budget is used (always keep at least one)."""
    chosen, used = [], 0
    for p in passages:
        cost = len(p.text) + 80
        if chosen and used + cost > max_chars:
            continue
        chosen.append(p)
        used += cost
    return chosen


def evidence_block(passages: list[Passage]) -> str:
    parts = []
    for n, p in enumerate(passages, 1):
        origin = "original source" if p.kind == "raw" else "generated wiki page"
        parts.append(f"[S{n}] {p.file} — {p.section} (lines {p.start_line}-{p.end_line}, {origin})\n{p.text}")
    return "\n\n".join(parts)


def build_ask(rules: str, question: str, passages: list[Passage]) -> list[dict]:
    if passages:
        evidence = evidence_block(passages)
    else:
        evidence = "(no passages were retrieved)"
    user = (
        f"EVIDENCE PASSAGES\n=================\n{evidence}\n\n"
        f"QUESTION\n========\n{question}\n\n"
        "Answer using only the passages above, citing them as [S#]. "
        "If they do not contain the answer, start with 'INSUFFICIENT EVIDENCE:'."
    )
    return [{"role": "system", "content": rules}, {"role": "user", "content": user}]


def build_chat(persona: str, capabilities: str, history: list[dict], message: str,
               passages: list[Passage] | None, retrieval_note: str) -> list[dict]:
    system = f"{persona}\n\n## Commands available to Matt in this CLI\n{capabilities}"
    messages = [{"role": "system", "content": system}, *history]
    if passages:
        content = (
            f"{message}\n\n"
            f"---\nNOTES FROM THE WIKI (retrieved for this message only; cite as [S#] when you use them)\n"
            f"{evidence_block(passages)}"
        )
    elif retrieval_note:
        content = f"{message}\n\n---\n({retrieval_note})"
    else:
        content = message
    messages.append({"role": "user", "content": content})
    return messages


ROUTER_SCHEMA = {
    "type": "object",
    "properties": {
        "needs_notes": {"type": "boolean"},
        "search_query": {"type": "string"},
    },
    "required": ["needs_notes", "search_query"],
}


def build_router(history: list[dict], message: str) -> list[dict]:
    recent = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in history[-4:]) or "(start of conversation)"
    system = (
        "You decide whether a chat message needs a lookup in the user's personal wiki of class project notes "
        "(a networking tracker web app, a Ms. Pac-Man DQN agent, a small nanoGPT model). "
        "needs_notes=true only when answering requires specific facts from those notes. "
        "Greetings, questions about the assistant, general brainstorming, and edits to a previous reply need no notes. "
        "If needs_notes is true, write a short keyword search_query that stands on its own; otherwise use an empty string."
    )
    user = f"Recent conversation:\n{recent}\n\nNew message: {message}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
