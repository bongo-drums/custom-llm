"""The retrieval tool: split sources into passages, index them, and search.

Default method is BM25 keyword scoring, implemented here in plain Python so that
`wiki search` needs no model and no download. The optional "hybrid" method adds
local embeddings (EmbeddingGemma through Ollama) and merges both rankings with
reciprocal-rank fusion. The index lives in .wiki_cache/, outside the vault.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, asdict, field
from pathlib import Path

from .config import Config
from .sources import SourceCatalog, parse_sections, read_text, iter_raw_files

INDEX_VERSION = 4

STOPWORDS = set("""
a an and are as at be but by can could did do does for from had has have how i if in into is it its
me my of on or our so than that the their them then there these they this to was we were what when
where which who why will with would you your about after also any each just more most not only other
some such very via up out over under all both one two use used using see
""".split())

NAV_SECTIONS = {"Related notes", "Sources", "Topics in this project"}

IMAGE_MD = re.compile(r"!\[[^\]]*\]\([^)]*\)|<img[^>]*>", re.I)
LINK_MD = re.compile(r"\[([^\]]+)\]\([^)]*\)")
TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")


def stem(word: str) -> str:
    """Very light suffix stripping so 'policies'~'policy', 'trained'~'train'."""
    for suffix, repl in (("ies", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)] + repl
    return word


def tokenize(text: str) -> list[str]:
    return [stem(t) for t in TOKEN.findall(text.lower()) if t not in STOPWORDS]


def display_clean(text: str) -> str:
    """Passage text for indexing/prompting: drop images and link URLs, keep words."""
    text = IMAGE_MD.sub("", text)
    return LINK_MD.sub(r"\1", text)


@dataclass
class Passage:
    id: str
    kind: str               # "raw" (original source) or "wiki" (generated page)
    file: str               # vault-relative path, e.g. raw/ms-pacman-README.md
    source_id: str          # catalog ID for raw; page title for wiki
    section: str            # heading path shown to readers
    heading: str            # the exact heading, for Obsidian [[file#heading]] links
    start_line: int
    end_line: int
    text: str               # cleaned passage text (no image tags or URLs)
    score: float = 0.0
    scores: dict = field(default_factory=dict)

    @property
    def location(self) -> str:
        return f"{self.file}:{self.start_line}-{self.end_line}"

    @property
    def obsidian_link(self) -> str:
        return f"[[{Path(self.file).stem}#{self.heading}]]"


def split_section(text: str, start_line: int, target: int) -> list[tuple[int, int, str]]:
    """Split one section into ~target-char windows on blank lines, keeping line ranges."""
    lines = text.splitlines()
    out, buf, buf_start, size = [], [], 0, 0
    for i, line in enumerate(lines):
        if not buf:
            buf_start = i
        buf.append(line)
        size += len(line) + 1
        if size >= target and (not line.strip() or i == len(lines) - 1):
            out.append((start_line + buf_start, start_line + i, "\n".join(buf)))
            buf, size = [], 0
    if buf:
        if out and size < target // 4:  # fold a tiny tail into the previous window
            s, _, t = out.pop()
            out.append((s, start_line + len(lines) - 1, t + "\n" + "\n".join(buf)))
        else:
            out.append((start_line + buf_start, start_line + len(lines) - 1, "\n".join(buf)))
    return out


def build_passages(cfg: Config) -> list[Passage]:
    vault = cfg.paths.vault
    catalog = SourceCatalog(cfg.paths.state / "source_catalog.json", vault)
    passages: list[Passage] = []

    files: list[tuple[str, Path]] = [("raw", p) for p in iter_raw_files(cfg.paths.raw)]
    if cfg.retrieval.include_wiki_pages and cfg.paths.wiki.exists():
        files += [("wiki", p) for p in sorted(cfg.paths.wiki.rglob("*.md"))]

    for kind, path in files:
        rel = path.resolve().relative_to(vault).as_posix()
        text = read_text(path)
        if kind == "wiki":
            text = _strip_frontmatter(text)
            source_id = path.stem
        else:
            entry = catalog.by_file(rel)
            source_id = entry.id if entry else path.stem
        offset = 0
        if kind == "wiki":
            offset = read_text(path).count("\n") - text.count("\n")
        for sec in parse_sections(text, path.stem):
            if kind == "wiki" and sec.heading in NAV_SECTIONS:
                continue  # link lists are navigation, not evidence
            for s, e, chunk in split_section(sec.text, sec.start_line, cfg.retrieval.chunk_chars):
                clean = display_clean(chunk).strip()
                if len(re.sub(r"[#|\-\s:*]", "", clean)) < 40:
                    continue  # heading-only or image-only windows carry no evidence
                pid = hashlib.sha1(f"{rel}:{s}:{e}:{clean}".encode()).hexdigest()[:12]
                passages.append(Passage(
                    id=pid, kind=kind, file=rel, source_id=source_id,
                    section=sec.label, heading=sec.heading,
                    start_line=s + offset, end_line=e + offset, text=clean,
                ))
    return passages


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end > 0:
            return text[end + 4:].lstrip("\n")
    return text


def _fingerprint(cfg: Config) -> str:
    h = hashlib.sha1(f"v{INDEX_VERSION}:{cfg.retrieval.chunk_chars}:{cfg.retrieval.include_wiki_pages}".encode())
    roots = [cfg.paths.raw] + ([cfg.paths.wiki] if cfg.retrieval.include_wiki_pages else [])
    for root in roots:
        if root.exists():
            for p in sorted(root.rglob("*")):
                if p.is_file():
                    st = p.stat()
                    h.update(f"{p}:{st.st_size}:{st.st_mtime_ns}".encode())
    return h.hexdigest()


class Index:
    """BM25 over passages; heading text is counted twice so section titles matter."""

    k1 = 1.4
    b = 0.75

    def __init__(self, passages: list[Passage]):
        self.passages = passages
        self.docs = [Counter(tokenize(f"{p.section} {p.section} {p.text}")) for p in passages]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = (sum(self.lengths) / len(self.lengths)) if self.lengths else 1.0
        df = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(passages)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    # ----- persistence -----
    @classmethod
    def load_or_build(cls, cfg: Config, rebuild: bool = False) -> tuple["Index", bool]:
        cache = cfg.paths.cache / "index.json"
        fp = _fingerprint(cfg)
        if not rebuild and cache.exists():
            data = json.loads(cache.read_text(encoding="utf-8"))
            if data.get("fingerprint") == fp:
                return cls([Passage(**p) for p in data["passages"]]), False
        index = cls(build_passages(cfg))
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"fingerprint": fp, "passages": [asdict(p) for p in index.passages]},
                                    ensure_ascii=False), encoding="utf-8")
        return index, True

    # ----- search -----
    def bm25(self, query: str) -> list[tuple[int, float]]:
        q = tokenize(query)
        scored = []
        for i, doc in enumerate(self.docs):
            s = 0.0
            for t in q:
                tf = doc.get(t)
                if tf:
                    norm = tf + self.k1 * (1 - self.b + self.b * self.lengths[i] / self.avg_len)
                    s += self.idf[t] * tf * (self.k1 + 1) / norm
            if s > 0:
                scored.append((i, s))
        return sorted(scored, key=lambda x: -x[1])

    def search(self, query: str, k: int, *, method: str = "bm25", embedder=None,
               kinds: tuple[str, ...] = ("raw", "wiki")) -> list[Passage]:
        allowed = [i for i, p in enumerate(self.passages) if p.kind in kinds]
        allowed_set = set(allowed)
        lexical = [(i, s) for i, s in self.bm25(query) if i in allowed_set]

        if method == "hybrid" and embedder is not None:
            dense = [(i, s) for i, s in embedder.rank(query, self.passages) if i in allowed_set]
            fused: dict[int, float] = {}
            for ranking in (lexical, dense):
                for rank, (i, _) in enumerate(ranking[:50]):
                    fused[i] = fused.get(i, 0.0) + 1.0 / (60 + rank)
            lex, den = dict(lexical), dict(dense)
            order = sorted(fused.items(), key=lambda x: -x[1])[:k]
            results = []
            for i, s in order:
                p = _copy(self.passages[i], s)
                p.scores = {"rrf": round(s, 4), "bm25": round(lex.get(i, 0.0), 3), "cosine": round(den.get(i, 0.0), 3)}
                results.append(p)
            return results

        results = []
        for i, s in lexical[:k]:
            p = _copy(self.passages[i], s)
            p.scores = {"bm25": round(s, 3)}
            results.append(p)
        return results


def _copy(p: Passage, score: float) -> Passage:
    q = Passage(**{**asdict(p), "score": round(score, 4)})
    return q


class Embedder:
    """Local embeddings via Ollama, cached per passage in .wiki_cache/embeddings.json."""

    def __init__(self, client, model: str, cache_dir: Path):
        self.client = client
        self.model = model
        self.path = cache_dir / "embeddings.json"
        self.cache: dict = {}
        if self.path.exists():
            self.cache = json.loads(self.path.read_text(encoding="utf-8")).get(model, {})

    def _vectors(self, passages: list[Passage]) -> list[list[float]]:
        missing = [p for p in passages if p.id not in self.cache]
        for start in range(0, len(missing), 16):
            batch = missing[start:start + 16]
            vecs = self.client.embed([f"{p.section}\n{p.text}" for p in batch], self.model)
            for p, v in zip(batch, vecs):
                self.cache[p.id] = v
        if missing:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({self.model: self.cache}), encoding="utf-8")
        return [self.cache[p.id] for p in passages]

    def rank(self, query: str, passages: list[Passage]) -> list[tuple[int, float]]:
        vecs = self._vectors(passages)
        q = self.client.embed([query], self.model)[0]
        scored = [(i, _cos(q, v)) for i, v in enumerate(vecs)]
        return sorted(scored, key=lambda x: -x[1])


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
