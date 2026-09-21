"""Stricter-than-notebook leakage audit: corpus/ vs evals/ (reads evals only to compare).

Flags any corpus line containing (a) a full eval prompt, (b) any complete
sentence from an eval prompt, or (c) the final prompt clause followed by its answer.
Run: python check_corpus_leakage.py
"""
import json, re
from pathlib import Path

norm = lambda s: " ".join(re.findall(r"\w+(?:['’]\w+)*|[^\w\s]", s.lower()))
cases = json.loads(Path("evals/language_evals.json").read_text())["cases"]
text = "\n".join(norm(l) for p in Path("corpus").rglob("*") if p.suffix in {".txt", ".md", ".pdf"} and p.name != "README.md"
                 for l in p.read_text(encoding="utf-8").splitlines())
problems = []
for c in cases:
    prompt = norm(c["prompt"])
    parts = [s.strip() for s in prompt.split(" . ") if s.strip()]
    checks = [("full prompt", prompt), ("prompt + answer", norm(parts[-1] + " " + c["answer"]))]
    checks += [("prompt sentence", s + " .") for s in parts[:-1]]
    for kind, needle in checks:
        if re.search(r"(^|\s)" + re.escape(needle) + r"(\s|$)", text):
            problems.append((c["id"], kind, needle))
print(f"Checked {len(cases)} cases against corpus/: {len(problems)} matches")
for p in problems:
    print("  ", p)
