"""Automatic citation checks on a generated answer.

These checks catch mechanical failures (citing a passage that was never shown,
uncited sentences, numbers that appear in no cited passage). They are a filter,
not proof: a human still opens each cited passage and judges support.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

from .index import Passage, tokenize

CITE = re.compile(r"\[S(\d+)\]")
NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?")
INSUFFICIENT = re.compile(r"insufficient evidence", re.I)


@dataclass
class CitationReport:
    status: str                              # cited | cited-with-gaps | insufficient | partial | uncited | invalid
    cited: list[int] = field(default_factory=list)
    invalid: list[int] = field(default_factory=list)
    uncited_sentences: list[str] = field(default_factory=list)
    unsupported_numbers: list[str] = field(default_factory=list)
    weak_support: list[str] = field(default_factory=list)
    insufficient: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        bits = [f"status={self.status}"]
        if self.cited:
            bits.append("cited=" + ",".join(f"S{i}" for i in self.cited))
        if self.invalid:
            bits.append("INVALID=" + ",".join(f"S{i}" for i in self.invalid))
        if self.uncited_sentences:
            bits.append(f"uncited_sentences={len(self.uncited_sentences)}")
        if self.unsupported_numbers:
            bits.append("numbers_not_in_cited=" + ",".join(self.unsupported_numbers))
        if self.weak_support:
            bits.append(f"weak_support={len(self.weak_support)}")
        return "  ".join(bits)


def _sentences(text: str) -> list[str]:
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.M)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z`*\[])|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 12]


def check(answer: str, passages: list[Passage], require_citations: bool = True) -> CitationReport:
    shown = set(range(1, len(passages) + 1))
    cited_all = [int(n) for n in CITE.findall(answer)]
    cited = sorted(set(cited_all) & shown)
    invalid = sorted(set(cited_all) - shown)
    insufficient = bool(INSUFFICIENT.search(answer))

    uncited, numbers_bad, weak = [], [], []
    for sent in _sentences(answer):
        if INSUFFICIENT.search(sent):
            continue
        ids = [int(n) for n in CITE.findall(sent) if int(n) in shown]
        if not ids:
            if require_citations and not sent.rstrip().endswith(":"):
                uncited.append(sent)
            continue
        support_text = " ".join(passages[i - 1].text for i in ids)
        support_norm = support_text.replace(",", "")
        for num in NUMBER.findall(CITE.sub("", sent)):
            n = num.replace(",", "").rstrip("%")
            if n and n not in support_norm:
                numbers_bad.append(num)
        words = {t for t in tokenize(CITE.sub("", sent)) if len(t) > 3}
        if words:
            overlap = len(words & set(tokenize(support_text))) / len(words)
            if overlap < 0.3:
                weak.append(sent)

    if invalid:
        status = "invalid"
    elif insufficient and not cited:
        status = "insufficient"
    elif insufficient:
        status = "partial"
    elif not cited:
        status = "uncited"
    elif uncited or numbers_bad or weak:
        status = "cited-with-gaps"
    else:
        status = "cited"
    return CitationReport(status, cited, invalid, uncited, sorted(set(numbers_bad)), weak, insufficient)
