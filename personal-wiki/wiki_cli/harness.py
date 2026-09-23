"""The harness: mode behaviour, routing, prompt assembly, model calls, checks, saved outputs.

  search  retrieval tool only -> passages          (no model)
  ask     retrieve -> research rules + evidence -> Gemma -> citation check -> evidence record
  chat    persona + capabilities + history -> [router decides: retrieve?] -> Gemma -> citation check
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from . import citations, prompts
from .config import Config
from .index import Embedder, Index, Passage
from .llm import ModelUnavailable, OllamaClient, internet_reachable

CAPABILITIES = """\
- `wiki chat`   talk with me (Scout): brainstorm, draft, plan; I look in your notes only when needed
- `wiki ask "question"`   one standalone factual answer from your notes, with citations, or "insufficient evidence"
- `wiki search "words"`   show the original matching passages and file paths, no AI answer
- `wiki ingest vault/raw` turn original sources into linked wiki pages and refresh the index
- inside chat: /notes <query> forces a notes lookup, /sources shows the last passages, /save saves my last reply as a draft,
  /reset clears this conversation, /exit quits"""


RAW_ONLY = ("raw",)              # ask + search default: original evidence only
RAW_AND_WIKI = ("raw", "wiki")   # chat: originals plus the generated summaries


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def slug(text: str, n: int = 6) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())[:n]
    return "-".join(words) or "run"


class Harness:
    def __init__(self, cfg: Config, client: OllamaClient | None = None):
        self.cfg = cfg
        self.client = client or OllamaClient(cfg.model)
        self._index: Index | None = None
        self.index_rebuilt = False

    # ---------------- retrieval tool ----------------
    @property
    def index(self) -> Index:
        if self._index is None:
            self._index, self.index_rebuilt = Index.load_or_build(self.cfg)
        return self._index

    def retrieve(self, query: str, k: int, kinds: tuple[str, ...] = RAW_ONLY) -> tuple[list[Passage], str]:
        """The retrieval tool. kinds=("raw",) searches original sources only; add "wiki" for generated pages."""
        method = self.cfg.retrieval.method
        if method == "hybrid":
            try:
                embedder = Embedder(self.client, self.cfg.retrieval.embedding_model, self.cfg.paths.cache)
                return self.index.search(query, k, method="hybrid", embedder=embedder, kinds=kinds), "hybrid"
            except ModelUnavailable as e:
                note = f"bm25 (hybrid unavailable: {str(e).splitlines()[0]})"
                return self.index.search(query, k, kinds=kinds), note
        return self.index.search(query, k, kinds=kinds), "bm25"

    def search(self, query: str, k: int, include_wiki: bool = False) -> dict:
        start = time.perf_counter()
        kinds = RAW_AND_WIKI if include_wiki else RAW_ONLY
        passages, method = self.retrieve(query, k, kinds)
        return {"mode": "search", "query": query, "method": method, "scope": list(kinds), "passages": passages,
                "seconds": round(time.perf_counter() - start, 3), "passage_count": len(self.index.passages)}

    # ---------------- ask: standalone RAG ----------------
    def ask(self, question: str, on_token=None) -> dict:
        rules = prompts.load_instruction(self.cfg.paths.instructions, "wiki-instructions.md")
        t0 = time.perf_counter()
        retrieved, method = self.retrieve(question, self.cfg.retrieval.top_k, RAW_ONLY)
        retrieval_s = time.perf_counter() - t0
        passages = prompts.select_passages(retrieved, self.cfg.retrieval.max_context_chars)
        messages = prompts.build_ask(rules, question, passages)  # note: no chat history, no persona

        self.client.ensure_ready()
        result = self.client.chat(messages, on_token=on_token)
        report = citations.check(result.text, passages)
        return {
            "mode": "ask",
            "execution": "local",
            "question": question,
            "retrieval": {"method": method, "scope": list(RAW_ONLY), "seconds": round(retrieval_s, 3), "top_k": self.cfg.retrieval.top_k,
                          "max_context_chars": self.cfg.retrieval.max_context_chars,
                          "sent_chars": sum(len(p.text) for p in passages)},
            "passages": passages,
            "prompt": messages,
            "answer": result.text,
            "citation_check": report,
            "timing": result.stats(),
        }

    # ---------------- evidence ----------------
    def environment(self) -> dict:
        return {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "execution": "local",
            "internet_reachable": internet_reachable(),
            "model": self.client.identity(),
            "memory": self.client.memory(),
            "config": {"num_ctx": self.cfg.model.num_ctx, "temperature": self.cfg.model.temperature,
                       "seed": self.cfg.model.seed, "retrieval": asdict(self.cfg.retrieval)},
        }

    def save_record(self, record: dict, folder: str, name: str) -> Path:
        out_dir = self.cfg.paths.evidence / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(_jsonable(record), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path


def _jsonable(obj):
    if isinstance(obj, Passage):
        d = asdict(obj)
        d["obsidian_link"] = obj.obsidian_link
        return d
    if isinstance(obj, citations.CitationReport):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj


# ---------------- chat: the personal assistant ----------------

META = re.compile(r"\b(what can (you|we|i)|help me with|who are you|what are you|how do (you|i) use|your (abilities|capabilities)|commands?)\b", re.I)
GREETING = re.compile(r"^\s*(hi|hey|hello|yo|thanks|thank you|ok(ay)?|cool|great|bye)\b[\s!.?]*$", re.I)
EDIT = re.compile(r"\b(make (that|it|this)|shorter|longer|shorten|rephrase|reword|rewrite|simplify|summari[sz]e (that|it)|"
                  r"turn (that|it) into|as bullets?|more (formal|casual|concise)|fix the tone|translate (that|it))\b", re.I)


@dataclass
class TurnDecision:
    retrieve: bool
    query: str
    reason: str


@dataclass
class ChatSession:
    harness: Harness
    history: list[dict] = field(default_factory=list)
    last_passages: list[Passage] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)
    started: str = field(default_factory=now_stamp)

    def __post_init__(self):
        cfg = self.harness.cfg
        self.persona = prompts.load_instruction(cfg.paths.instructions, "persona.md")

    def decide(self, message: str) -> TurnDecision:
        """Harness-side routing: cheap rules first, then a tiny Gemma classification call."""
        if message.lower().startswith("/notes"):
            q = message[6:].strip()
            return TurnDecision(bool(q), q, "user forced a notes lookup with /notes")
        if GREETING.match(message):
            return TurnDecision(False, "", "greeting / small talk")
        if META.search(message):
            return TurnDecision(False, "", "question about the assistant's capabilities")
        if EDIT.search(message) and self.history:
            return TurnDecision(False, "", "follow-up edit of the previous reply (uses conversation, not notes)")
        data, _ = self.harness.client.chat_json(prompts.build_router(self.history, message), prompts.ROUTER_SCHEMA)
        if data.get("needs_notes") and str(data.get("search_query", "")).strip():
            return TurnDecision(True, data["search_query"].strip(), "router: the message needs facts from the notes")
        return TurnDecision(False, "", "router: answerable from the conversation alone")

    def send(self, message: str, on_token=None, on_decision=None) -> dict:
        cfg = self.harness.cfg
        decision = self.decide(message)
        if on_decision:
            on_decision(decision)
        passages: list[Passage] = []
        note = ""
        if decision.retrieve:
            kinds = RAW_AND_WIKI if cfg.retrieval.include_wiki_pages else RAW_ONLY
            found, method = self.harness.retrieve(decision.query, cfg.chat.chat_top_k, kinds)
            passages = prompts.select_passages(found, cfg.retrieval.max_context_chars)
            if not passages:
                note = "The notes were searched and nothing relevant was found. Say so plainly and offer other help."
        user_text = message[6:].strip() if message.lower().startswith("/notes") else message
        keep = cfg.chat.history_turns * 2
        messages = prompts.build_chat(self.persona, CAPABILITIES, self.history[-keep:], user_text, passages, note)

        result = self.harness.client.chat(messages, on_token=on_token)
        report = citations.check(result.text, passages, require_citations=False) if passages else None
        # History keeps the plain user message and the reply. Retrieved passages are NOT stored as history,
        # so later turns cannot mistake an old reply for verified evidence.
        self.history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": result.text}]
        self.last_passages = passages
        turn = {
            "user": message,
            "decision": asdict(decision),
            "passages": [{"tag": f"S{i}", "location": p.location, "section": p.section} for i, p in enumerate(passages, 1)],
            "reply": result.text,
            "citation_check": report.to_dict() if report else None,
            "timing": result.stats(),
        }
        self.log.append(turn)
        return turn

    def reset(self):
        self.history.clear()
        self.last_passages = []

    def save_transcript(self, name: str | None = None) -> Path:
        record = {"mode": "chat", "execution": "local", "environment": self.harness.environment(), "turns": self.log}
        path = self.harness.save_record(record, "chat", name or f"chat-{self.started}")
        md = [f"# Chat transcript ({self.started}, local)", ""]
        for t in self.log:
            d = t["decision"]
            md += [f"**You:** {t['user']}", "",
                   f"_harness: {'retrieved notes for “' + d['query'] + '”' if d['retrieve'] else 'no notes lookup'} "
                   f"— {d['reason']}; {t['timing']['wall_seconds']}s_", ""]
            if t["passages"]:
                md += ["_passages: " + "; ".join(f"[{p['tag']}] {p['location']} ({p['section']})" for p in t["passages"]) + "_", ""]
            md += [f"**Scout:** {t['reply']}", ""]
            if t["citation_check"]:
                md += [f"_citation check: {t['citation_check']['status']}_", ""]
        path.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
        return path

    def save_draft(self, drafts_dir: Path) -> Path | None:
        last = next((m["content"] for m in reversed(self.history) if m["role"] == "assistant"), None)
        if not last:
            return None
        drafts_dir.mkdir(parents=True, exist_ok=True)
        first_user = next((m["content"] for m in reversed(self.history) if m["role"] == "user"), "draft")
        path = drafts_dir / f"{now_stamp()}-{slug(first_user)}.md"
        path.write_text(
            "---\ntype: chat-draft\nnot_evidence: true   # generated by chat; never indexed or cited\n---\n\n" + last + "\n",
            encoding="utf-8")
        return path
