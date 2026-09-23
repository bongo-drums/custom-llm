"""Read original sources, keep a source catalog, and split Markdown into sections.

Originals in vault/raw/ are only ever read, never written. The catalog maps each
machine source ID and original filename to a readable project title, and records
a SHA-256 hash so anyone can confirm the raw file is unchanged.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

SUPPORTED = {".md", ".markdown", ".txt"}
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


@dataclass
class Section:
    heading: str            # e.g. "Authentication and ownership"
    path: list[str]         # e.g. ["Networking Tracker", "Authentication and ownership"]
    level: int
    start_line: int         # 1-based, inclusive (the heading line itself)
    end_line: int           # 1-based, inclusive
    text: str               # original lines, unchanged

    @property
    def label(self) -> str:
        return " > ".join(self.path[1:] or self.path)


@dataclass
class SourceEntry:
    id: str                 # machine ID, e.g. "src-ms-pacman"
    file: str               # path relative to the vault, e.g. "raw/ms-pacman-README.md"
    title: str              # readable project title used for the project note
    origin: str = ""        # where the original came from
    sha256: str = ""
    description: str = ""


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path: Path) -> str:
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError(f"Unsupported file type {path.suffix!r} for {path.name}. Supported: {', '.join(sorted(SUPPORTED))}")
    return path.read_text(encoding="utf-8")


def parse_sections(text: str, fallback_title: str) -> list[Section]:
    """Split Markdown by headings (ignoring '#' inside code fences), keeping line numbers."""
    lines = text.splitlines()
    heads: list[tuple[int, int, str]] = []  # (line_index, level, heading)
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if not in_fence:
            m = HEADING.match(line)
            if m:
                heads.append((i, len(m.group(1)), clean_heading(m.group(2))))

    sections: list[Section] = []
    if not heads or heads[0][0] > 0:
        first = heads[0][0] if heads else len(lines)
        body = "\n".join(lines[:first])
        if body.strip():
            sections.append(Section(fallback_title, [fallback_title], 1, 1, max(first, 1), body))

    stack: list[tuple[int, str]] = []
    for n, (i, level, heading) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, heading))
        sections.append(Section(
            heading=heading,
            path=[h for _, h in stack],
            level=level,
            start_line=i + 1,
            end_line=end,
            text="\n".join(lines[i:end]),
        ))
    return sections


def clean_heading(h: str) -> str:
    """Heading text as Obsidian shows it (strip Markdown emphasis/links)."""
    h = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", h)
    return re.sub(r"[*_`]", "", h).strip()


def first_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        m = HEADING.match(line)
        if m and len(m.group(1)) == 1:
            return clean_heading(m.group(2))
    return fallback


class SourceCatalog:
    """state/source_catalog.json: source IDs <-> original files <-> readable titles."""

    def __init__(self, path: Path, vault: Path):
        self.path = path
        self.vault = vault
        self.entries: dict[str, SourceEntry] = {}
        if path.exists():
            for item in json.loads(path.read_text(encoding="utf-8"))["sources"]:
                entry = SourceEntry(**item)
                self.entries[entry.id] = entry

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"sources": [asdict(e) for e in sorted(self.entries.values(), key=lambda e: e.id)]}
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def by_file(self, rel: str) -> SourceEntry | None:
        return next((e for e in self.entries.values() if e.file == rel), None)

    def register(self, raw_file: Path) -> tuple[SourceEntry, bool]:
        """Return the catalog entry for a raw file, creating one if new. Second value: content changed."""
        rel = raw_file.resolve().relative_to(self.vault).as_posix()
        digest = sha256_of(raw_file)
        entry = self.by_file(rel)
        if entry is None:
            stem = re.sub(r"[^a-z0-9]+", "-", raw_file.stem.lower()).strip("-")
            stem = re.sub(r"-readme$", "", stem) or "source"
            title = first_title(raw_file.read_text(encoding="utf-8"), raw_file.stem)
            title = title.split(":")[0].strip()
            entry = SourceEntry(id=f"src-{stem}", file=rel, title=title, sha256=digest)
            self.entries[entry.id] = entry
            return entry, True
        changed = entry.sha256 != digest
        entry.sha256 = digest
        return entry, changed

    def verify(self) -> list[str]:
        """Problems found when checking every raw file against its recorded hash."""
        problems = []
        for e in self.entries.values():
            p = self.vault / e.file
            if not p.exists():
                problems.append(f"{e.id}: missing file {e.file}")
            elif e.sha256 and sha256_of(p) != e.sha256:
                problems.append(f"{e.id}: {e.file} changed since it was catalogued")
        return problems


def iter_raw_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.exists():
        raise FileNotFoundError(f"No such file or folder: {target}")
    files = sorted(p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)
    if not files:
        raise FileNotFoundError(f"No .md or .txt sources found in {target}")
    return files
