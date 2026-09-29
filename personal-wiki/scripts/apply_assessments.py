"""Stamp my human assessments (evals/assessments.json) into the saved evidence cards.

    python scripts/apply_assessments.py

Re-renders evidence/ask/test-*.md from the saved JSON records without calling the model,
so the answers, passages and timings stay exactly as the offline run produced them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from wiki_cli.citations import CitationReport  # noqa: E402
from wiki_cli.evals import card  # noqa: E402
from wiki_cli.index import Passage  # noqa: E402


def main() -> None:
    assessments = json.loads((ROOT / "evals" / "assessments.json").read_text(encoding="utf-8"))
    for path in sorted((ROOT / "evidence" / "ask").glob("test-*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        verdict = assessments.get(record["test"]["id"])
        if not verdict:
            continue
        record["human_assessment"] = verdict
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        view = dict(record)
        view["passages"] = [Passage(**{k: v for k, v in p.items() if k != "obsidian_link"}) for p in record["passages"]]
        view["citation_check"] = CitationReport(**record["citation_check"])
        path.with_suffix(".md").write_text(card(record["test"], view), encoding="utf-8")
        print(f"applied to {path.stem}")


if __name__ == "__main__":
    main()
