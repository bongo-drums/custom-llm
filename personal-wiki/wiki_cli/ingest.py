"""Ingestion: original source -> local Gemma -> reviewed, linked Obsidian notes.

Division of labour:
  Gemma decides   WHAT to write (topics, summaries, fact bullets, related-note reasons)
  the harness decides WHERE and HOW (filenames, folders, frontmatter, source links,
                   dedupe/merge, link validation, index.md, retrieval index)

This split keeps note names readable and links unbroken even when a small model
produces sloppy output: every title is sanitised, every section name is checked
against the real source outline, every link target must exist.

Re-ingestion: state/pages.json records each page's content per source ID.
Ingesting a source again *replaces that source's contributions* and never adds a
second page for the same subject (titles are matched exactly and fuzzily).
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import Config
from .index import Index, display_clean, tokenize
from .llm import OllamaClient
from .prompts import load_instruction
from .sources import SourceCatalog, Section, parse_sections, read_text

CATEGORIES = ("Concepts", "Tools")
PROJECT_FOLDER = "Projects"
MAX_TOPICS = 5
SECTION_TEXT_BUDGET = 5000   # chars of original text sent to Gemma per note
OUTLINE_PREVIEW = 160        # chars of each section shown in the planning outline

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "project_summary": {"type": "string"},
        "key_facts": {
            "type": "array",
            "items": {"type": "object", "properties": {"text": {"type": "string"}, "section": {"type": "string"}},
                      "required": ["text", "section"]},
        },
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "category": {"type": "string", "enum": list(CATEGORIES)},
                    "sections": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "category", "sections"],
            },
        },
    },
    "required": ["project_summary", "key_facts", "topics"],
}

NOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "details": {
            "type": "array",
            "items": {"type": "object", "properties": {"text": {"type": "string"}, "section": {"type": "string"}},
                      "required": ["text", "section"]},
        },
    },
    "required": ["summary", "details"],
}

LINK_SCHEMA = {
    "type": "object",
    "properties": {
        "links": {
            "type": "array",
            "items": {"type": "object", "properties": {"title": {"type": "string"}, "reason": {"type": "string"}},
                      "required": ["title", "reason"]},
        }
    },
    "required": ["links"],
}

MERGE_SCHEMA = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}


# ---------------------------------------------------------------- titles

FORBIDDEN_CHARS = re.compile(r'[\[\]#^|<>:"/\\?*`]')
HASHLIKE = re.compile(r"\b(?=[0-9a-f]*\d)[0-9a-f]{6,}\b", re.I)
DATELIKE = re.compile(r"\b\d{4}[-_/]\d{2}|\b\d{8}\b")
# README scaffolding, not subjects: a note called "Screenshots" or "Key Takeaways" tells a reader nothing.
GENERIC_TITLES = {
    "contents", "table of contents", "overview", "introduction", "intro", "summary", "features", "screenshots",
    "setup", "local setup", "installation", "usage", "run it yourself", "how to run", "key takeaways", "takeaways",
    "results", "files", "testing", "tests", "deployment", "limitations", "known limitations", "next steps",
    "what i observed", "what i expected", "what i would do next", "repository layout", "repository map",
    "reflection", "evidence", "conclusion", "notes", "details", "background", "project", "readme",
}
SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "vs", "with"}


def sanitize_title(raw: str) -> str | None:
    """Return a short readable note title, or None if the proposal is machine-like or a sentence."""
    if (raw or "").strip().endswith("?"):
        return None  # questions are not subjects
    t = FORBIDDEN_CHARS.sub(" ", raw or "")
    t = re.sub(r"\([^)]*\)?|\)", " ", t)          # drop parentheticals, including a dangling "(all"
    t = re.sub(r"^(my|our|the)\s+", "", t.strip(), flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" .,-_'")
    if t.lower() in GENERIC_TITLES:
        return None
    if not t or HASHLIKE.search(t) or DATELIKE.search(t):
        return None
    words = t.split(" ")
    if not 1 <= len(words) <= 6 or t.lower().startswith(("section", "chapter", "part ")):
        return None
    if re.fullmatch(r"[\d\s.\-]+", t):
        return None
    out = []
    for i, w in enumerate(words):
        if w.islower() and (i == 0 or w not in SMALL_WORDS):
            w = w[0].upper() + w[1:]
        out.append(w)
    return " ".join(out)


def title_key(title: str) -> str:
    return "-".join(tokenize(title)) or title.lower()


def similar(a: str, b: str) -> bool:
    ta, tb = set(tokenize(a)), set(tokenize(b))
    if not ta or not tb:
        return False
    return ta == tb or len(ta & tb) / len(ta | tb) >= 0.67


# ---------------------------------------------------------------- state

@dataclass
class Page:
    title: str
    category: str                    # Projects | Concepts | Tools
    kind: str                        # project | topic
    contributions: dict = field(default_factory=dict)   # source_id -> {summary, details, sections}
    related: dict = field(default_factory=dict)         # title -> reason (Gemma-proposed, validated)
    summary: str = ""
    file: str = ""                   # vault-relative path last written
    source_ids: list = field(default_factory=list)      # for project notes: the source they describe

    @property
    def rel_path(self) -> str:
        return f"wiki/{self.category}/{self.title}.md"


class PageStore:
    def __init__(self, path: Path):
        self.path = path
        self.pages: dict[str, Page] = {}
        if path.exists():
            for key, data in json.loads(path.read_text(encoding="utf-8"))["pages"].items():
                self.pages[key] = Page(**data)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"pages": {k: vars(p) for k, p in sorted(self.pages.items())}}
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def find(self, title: str) -> str | None:
        key = title_key(title)
        if key in self.pages:
            return key
        for k, p in self.pages.items():
            if similar(p.title, title):
                return k
        return None

    def titles(self) -> list[str]:
        return [p.title for p in self.pages.values()]


# ---------------------------------------------------------------- helpers

def _match_section(name: str, sections: list[Section]) -> Section | None:
    name_l = (name or "").strip().lower()
    for s in sections:
        if name_l in (s.label.lower(), s.heading.lower()):
            return s
    want = set(tokenize(name))
    best, best_score = None, 0.0
    for s in sections:
        have = set(tokenize(s.label))
        if want and have:
            score = len(want & have) / len(want | have)
            if score > best_score:
                best, best_score = s, score
    return best if best_score >= 0.5 else None


def _clean_text(text: str) -> str:
    text = re.sub(r"\[\[|\]\]", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _grounded(text: str, section: Section) -> tuple[bool, str]:
    """Drop bullets whose numbers do not appear in the cited section (a common small-model invention)."""
    src = section.text.replace(",", "")
    for n in NUM.findall(text):
        if n.replace(",", "") not in src:
            return False, f"number {n} not found in section '{section.label}'"
    words = {w for w in tokenize(text) if len(w) > 3}
    if words:
        overlap = len(words & set(tokenize(section.text))) / len(words)
        if overlap < 0.25:
            return False, f"only {overlap:.0%} of its words appear in section '{section.label}'"
    return True, ""


def _outline(sections: list[Section]) -> str:
    rows = []
    for s in sections:
        preview = display_clean(s.text.split("\n", 1)[1] if "\n" in s.text else "")
        preview = re.sub(r"\s+", " ", preview).strip()[:OUTLINE_PREVIEW]
        rows.append(f"- {s.label}: {preview}")
    return "\n".join(rows)


def _section_text(chosen: list[Section]) -> str:
    parts, used = [], 0
    for s in chosen:
        body = display_clean(s.text).strip()
        room = SECTION_TEXT_BUDGET - used
        if room <= 200:
            break
        body = body[:room]
        parts.append(f"### SECTION: {s.label}\n{body}")
        used += len(body)
    return "\n\n".join(parts)


# ---------------------------------------------------------------- main pipeline

class Ingestor:
    def __init__(self, cfg: Config, client: OllamaClient, log=print):
        self.cfg = cfg
        self.client = client
        self.log = log
        self.rules = load_instruction(cfg.paths.instructions, "ingest-instructions.md")
        self.catalog = SourceCatalog(cfg.paths.state / "source_catalog.json", cfg.paths.vault)
        self.store = PageStore(cfg.paths.state / "pages.json")
        self.report: dict = {"sources": [], "dropped_bullets": [], "dropped_topics": [], "dropped_links": [],
                             "calls": [], "skipped_reviewed": [], "removed_pages": []}

    def _call(self, purpose: str, user: str, schema: dict) -> dict:
        messages = [{"role": "system", "content": self.rules}, {"role": "user", "content": user}]
        data, result = self.client.chat_json(messages, schema)
        self.report["calls"].append({"purpose": purpose, **result.stats()})
        self.log(f"    · {purpose}: {result.seconds:.1f}s")
        return data

    # ---- one source ----
    def ingest_file(self, raw_file: Path) -> None:
        entry, changed = self.catalog.register(raw_file)
        text = read_text(raw_file)
        sections = parse_sections(text, entry.title)
        self.log(f"  {entry.file}  ->  source {entry.id}  ({len(sections)} sections{', new/changed' if changed else ''})")

        existing_topics = [p.title for p in self.store.pages.values() if p.kind == "topic"]
        plan = self._call(
            f"plan {entry.id}",
            f"SOURCE DOCUMENT: {entry.title}\n\nOUTLINE (section name: opening words)\n{_outline(sections)}\n\n"
            f"EXISTING NOTE TITLES (reuse one exactly if it is the same subject):\n"
            f"{', '.join(existing_topics) or '(none yet)'}\n\n"
            f"Return: project_summary (2 sentences about this project), key_facts (3-5 facts, each with the exact "
            f"section name), and topics (3-{MAX_TOPICS} topics with title, category, and exact section names).",
            PLAN_SCHEMA,
        )

        # Forget what this source contributed last time; this run replaces it.
        for page in self.store.pages.values():
            page.contributions.pop(entry.id, None)

        # Project note (title comes from the source catalog, never from the model).
        pkey = title_key(entry.title)
        project = self.store.pages.get(pkey) or Page(entry.title, PROJECT_FOLDER, "project")
        project.source_ids = [entry.id]
        facts = self._validated_details(plan.get("key_facts", []), sections, entry.title)
        project.contributions[entry.id] = {
            "summary": _clean_text(plan.get("project_summary", "")),
            "details": facts,
            "sections": sorted({d["section"] for d in facts}),
        }
        self.store.pages[pkey] = project

        project_titles = {p.title.lower() for p in self.store.pages.values() if p.kind == "project"}
        seen_keys = set()
        for topic in plan.get("topics", [])[:MAX_TOPICS]:
            title = sanitize_title(topic.get("title", ""))
            chosen: list[Section] = []
            for name in topic.get("sections", []):
                sec = _match_section(name, sections)
                if sec and sec not in chosen:
                    chosen.append(sec)
            reason = None
            if not title:
                reason = "title is not a short readable subject name"
            elif title.lower() in project_titles or similar(title, entry.title):
                reason = "duplicates the project note"
            elif not chosen:
                reason = "none of its section names exist in the source"
            if reason:
                self.report["dropped_topics"].append({"source": entry.id, "proposed": topic.get("title"), "reason": reason})
                continue

            key = self.store.find(title) or title_key(title)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            page = self.store.pages.get(key)
            if page is None:
                category = topic.get("category") if topic.get("category") in CATEGORIES else "Concepts"
                page = Page(title, category, "topic")
                self.store.pages[key] = page

            note = self._call(
                f"write '{page.title}'",
                f"NOTE TITLE: {page.title}\nPROJECT: {entry.title}\n\nSOURCE TEXT (use only this):\n{_section_text(chosen)}\n\n"
                f"Return summary (1-2 sentences) and details (3-6 bullets, each with the exact section name "
                f"from the '### SECTION:' lines above).",
                NOTE_SCHEMA,
            )
            details = self._validated_details(note.get("details", []), chosen, page.title)
            if not details:
                self.report["dropped_topics"].append({"source": entry.id, "proposed": page.title,
                                                      "reason": "no bullet survived grounding checks"})
                continue
            page.contributions[entry.id] = {
                "summary": _clean_text(note.get("summary", "")),
                "details": details,
                "sections": sorted({d["section"] for d in details}),
            }

        self.report["sources"].append({"id": entry.id, "file": entry.file, "sha256": entry.sha256,
                                       "sections": len(sections), "changed": changed})

    def _validated_details(self, items: list[dict], sections: list[Section], note: str) -> list[dict]:
        out = []
        for item in items[:6]:
            text = _clean_text(item.get("text", ""))
            sec = _match_section(item.get("section", ""), sections)
            if not text:
                continue
            if sec is None:
                # fall back to the section that actually contains most of the bullet's words
                sec = max(sections, key=lambda s: len(set(tokenize(text)) & set(tokenize(s.text))))
            ok, why = _grounded(text, sec)
            if not ok:
                self.report["dropped_bullets"].append({"note": note, "text": text, "reason": why})
                continue
            out.append({"text": text, "section": sec.label, "heading": sec.heading,
                        "lines": [sec.start_line, sec.end_line]})
        return out

    # ---- after all sources ----
    def finalize(self, link_titles: set[str] | None = None) -> None:
        # Pages whose every contribution disappeared (a source was re-ingested and dropped the topic).
        for key in [k for k, p in self.store.pages.items() if not p.contributions]:
            self.report["removed_pages"].append(self.store.pages[key].title)
            del self.store.pages[key]

        for page in self.store.pages.values():
            summaries = [c["summary"] for c in page.contributions.values() if c.get("summary")]
            if len(summaries) > 1 and (link_titles is None or page.title in link_titles):
                merged = self._call(
                    f"merge summary '{page.title}'",
                    f"Combine these summaries of the note '{page.title}' into 1-2 sentences, keeping only what they say:\n- "
                    + "\n- ".join(summaries), MERGE_SCHEMA)
                page.summary = _clean_text(merged.get("summary", "")) or summaries[0]
            elif len(summaries) == 1 or not page.summary:
                page.summary = summaries[0] if summaries else ""

        topics = [p for p in self.store.pages.values() if p.kind == "topic"]
        for page in topics:
            if link_titles is not None and page.title not in link_titles:
                continue
            candidates = [p for p in topics if p is not page]
            if not candidates:
                page.related = {}
                continue
            listing = "\n".join(f"- {p.title}: {p.summary[:160]}" for p in candidates)
            data = self._call(
                f"link '{page.title}'",
                f"NOTE: {page.title}\nSUMMARY: {page.summary}\n\nCANDIDATE NOTES:\n{listing}\n\n"
                "Pick at most 3 genuinely related candidate notes (exact titles) with a short reason each.",
                LINK_SCHEMA,
            )
            valid = {p.title.lower(): p.title for p in candidates}
            related = {}
            for link in data.get("links", [])[:3]:
                target = valid.get(str(link.get("title", "")).strip().lower())
                if target:
                    related[target] = _clean_text(link.get("reason", ""))[:140]
                else:
                    self.report["dropped_links"].append({"from": page.title, "to": link.get("title"),
                                                         "reason": "no note with that title"})
            page.related = related

        # Links may point at pages removed above; drop them so nothing dangles.
        titles = {p.title for p in self.store.pages.values()}
        for page in self.store.pages.values():
            page.related = {t: r for t, r in page.related.items() if t in titles}

        self.write_vault()
        self.store.save()
        self.catalog.save()

    # ---- rendering ----
    def write_vault(self) -> None:
        wiki = self.cfg.paths.wiki
        vault = self.cfg.paths.vault
        wanted = set()
        for page in self.store.pages.values():
            path = vault / page.rel_path
            wanted.add(path.resolve())
            if page.file and page.file != page.rel_path:
                old = vault / page.file
                if old.exists() and not _is_reviewed(old):
                    old.unlink()
            if path.exists() and _is_reviewed(path):
                self.report["skipped_reviewed"].append(page.title)
                page.file = page.rel_path
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.render(page), encoding="utf-8")
            page.file = page.rel_path

        # Remove generated files that no longer correspond to a page (never touches reviewed notes).
        for p in wiki.rglob("*.md"):
            if p.resolve() not in wanted and _is_generated(p) and not _is_reviewed(p):
                p.unlink()
        for d in sorted((d for d in wiki.rglob("*") if d.is_dir()), reverse=True):
            if not any(d.iterdir()):
                d.rmdir()
        write_index(self.cfg, self.store, self.catalog)

    def render(self, page: Page) -> str:
        catalog = self.catalog.entries
        by_title = {p.title: p for p in self.store.pages.values()}
        sources = []
        for sid, contrib in sorted(page.contributions.items()):
            entry = catalog.get(sid)
            if entry:
                sources.append((sid, entry, contrib))

        fm = ["---", f"title: {page.title}", f"type: {page.kind}", f"category: {page.category}",
              f"source_ids: [{', '.join(sid for sid, _, _ in sources)}]",
              "source_files:"]
        fm += [f"  - {entry.file}" for _, entry, _ in sources]
        fm += [f"generated_by: {self.client.cfg.name} via local Ollama",
               f"updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
               "reviewed: false   # set to true after checking against the sources; ingest will then leave this file alone",
               "---", ""]

        body = [f"# {page.title}", "", page.summary or "_No summary yet._", ""]

        if page.kind == "project":
            entry = sources[0][1] if sources else None
            if entry and entry.description:
                body += [f"> {entry.description}", ""]
            facts = [d for _, _, c in sources for d in c["details"]]
            if facts:
                body += ["## Key facts", ""]
                body += [f"- {d['text']} ({_src_link(entry, d)})" for d in facts]
                body.append("")
            topics = sorted((p for p in self.store.pages.values()
                             if p.kind == "topic" and any(s in p.contributions for s in page.source_ids)),
                            key=lambda p: p.title)
            if topics:
                body += ["## Topics in this project", ""]
                body += [f"- [[{t.title}]] — {_first_sentence(t.summary)}" for t in topics]
                body.append("")
        else:
            body += ["## Details", ""]
            multi = len(sources) > 1
            for sid, entry, contrib in sources:
                if multi:
                    body += [f"### In [[{entry.title}]]", ""]
                body += [f"- {d['text']} ({_src_link(entry, d)})" for d in contrib["details"]]
                body.append("")
            body += ["## Related notes", ""]
            for sid, entry, _ in sources:
                if entry.title in by_title:
                    body.append(f"- [[{entry.title}]] — the project where this topic comes up.")
            for title, reason in sorted(page.related.items()):
                body.append(f"- [[{title}]] — {reason or 'related topic.'}")
            body.append("")

        body += ["## Sources", ""]
        for sid, entry, contrib in sources:
            heads = {}
            for d in contrib["details"]:
                heads[d["heading"]] = d["lines"]
            body.append(f"- [[{Path(entry.file).stem}]] (`{entry.file}`, source ID `{sid}`)")
            for heading, (a, b) in heads.items():
                body.append(f"  - [[{Path(entry.file).stem}#{heading}]] — lines {a}–{b}")
        body.append("")
        return "\n".join(fm + body)


def _src_link(entry, detail: dict) -> str:
    return f"[[{Path(entry.file).stem}#{detail['heading']}|source]]"


def _first_sentence(text: str) -> str:
    m = re.match(r"(.+?[.!?])(\s|$)", text or "")
    return (m.group(1) if m else text or "").strip()


def _is_reviewed(path: Path) -> bool:
    head = path.read_text(encoding="utf-8")[:2000]
    return bool(re.search(r"^reviewed:\s*true\b", head, re.M))


def _is_generated(path: Path) -> bool:
    head = path.read_text(encoding="utf-8")[:2000]
    return "via local Ollama" in head


def write_index(cfg: Config, store: PageStore, catalog: SourceCatalog) -> None:
    groups = {PROJECT_FOLDER: [], "Concepts": [], "Tools": []}
    for p in store.pages.values():
        groups.setdefault(p.category, []).append(p)
    blurbs = {
        PROJECT_FOLDER: "One note per original source: what the project was and its key facts.",
        "Concepts": "Ideas and techniques that came up across the projects.",
        "Tools": "Named software, libraries and services the projects used.",
    }
    lines = [
        "# Personal Wiki: My Class Projects", "",
        "My notes on the projects I built in class. Start with a project, then follow its topic links. "
        "Every generated note links back to the exact section of the original write-up in `raw/`.", "",
    ]
    for group in (PROJECT_FOLDER, "Concepts", "Tools"):
        pages = sorted(groups.get(group, []), key=lambda p: p.title.lower())
        if not pages:
            continue
        lines += [f"## {group}", "", f"_{blurbs[group]}_", ""]
        lines += [f"- [[{p.title}]] — {_first_sentence(p.summary)}" for p in pages]
        lines.append("")
    lines += ["## Original sources", "", "Unchanged originals. IDs and hashes are in `state/source_catalog.json` "
              "(outside the vault).", ""]
    for e in sorted(catalog.entries.values(), key=lambda e: e.title):
        lines.append(f"- [[{Path(e.file).stem}]] — {e.title} (`{e.id}`). {e.description}")
    lines += ["", f"_Index generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by `wiki ingest`._", ""]
    cfg.paths.index_md.write_text("\n".join(lines), encoding="utf-8")


def run_ingest(cfg: Config, client: OllamaClient, files: list[Path], log=print, relink_all: bool = False) -> dict:
    start = time.perf_counter()
    ing = Ingestor(cfg, client, log)
    before = {p.title for p in ing.store.pages.values()}
    ingested_ids = []
    for f in files:
        ing.ingest_file(f)
        ingested_ids.append(ing.report["sources"][-1]["id"])
    # Re-link pages that this run touched (all pages on a full ingest).
    touched = {p.title for p in ing.store.pages.values()
               if relink_all or any(sid in p.contributions for sid in ingested_ids) or p.title not in before}
    ing.finalize(link_titles=None if relink_all else touched)
    after = {p.title for p in ing.store.pages.values()}
    ing.report.update({
        "pages_before": len(before), "pages_after": len(after),
        "created": sorted(after - before), "removed": sorted(before - after),
        "updated": sorted(touched & before & after),
        "seconds": round(time.perf_counter() - start, 1),
    })
    Index.load_or_build(cfg, rebuild=True)
    return ing.report
