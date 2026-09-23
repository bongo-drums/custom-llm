"""Run the fixed ask-mode tests and write one evidence card per test.

Retrieval and the answer are judged separately:
  1. retrieval  did an expected source section appear in the passages sent to Gemma?
  2. answer     does it mention the expected facts, cite passages, and (test 4) admit missing evidence?
The automatic checks are a first filter. Each card ends with a "Human assessment"
line that I fill in only after opening the cited passages myself.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import prompts
from .harness import Harness, _jsonable
from .index import Passage


def _expected_hit(expected: dict, passages: list[Passage]) -> int | None:
    """Rank of the first passage from the expected file and section ('A || B' lists acceptable sections)."""
    wants = [w.strip().lower() for w in expected["section"].split("||")]
    for rank, p in enumerate(passages, 1):
        sec = p.section.lower()
        if p.kind == "raw" and p.file == expected["file"] and any(w == sec or w in sec or sec in w for w in wants):
            return rank
    return None


def _mentions(answer: str, patterns: list[str]) -> dict:
    low = answer.lower()
    return {pat: bool(re.search(pat, low)) for pat in patterns}


def run_eval(h: Harness, questions_path: Path, only: list[str] | None = None, log=print) -> list[dict]:
    tests = json.loads(questions_path.read_text(encoding="utf-8"))["tests"]
    # My own judgements live in a separate file so rerunning the eval never overwrites them.
    assess_path = questions_path.parent / "assessments.json"
    assessments = json.loads(assess_path.read_text(encoding="utf-8")) if assess_path.exists() else {}
    env = h.environment()
    out_dir = h.cfg.paths.evidence / "ask"
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for t in tests:
        if only and t["id"] not in only:
            continue
        log(f"\n=== {t['id']}: {t['question']}")
        run = h.ask(t["question"])
        passages: list[Passage] = run["passages"]
        hits = {e["section"]: _expected_hit(e, passages) for e in t["expected_sources"]}
        mention = _mentions(run["answer"], t.get("must_mention", []))
        cc = run["citation_check"]
        auto = {
            "retrieval_found_expected": all(v is not None for v in hits.values()) if hits else None,
            "expected_ranks": hits,
            "mentions_expected_facts": mention,
            "citation_status": cc.status,
        }
        if t.get("expect_insufficient"):
            auto["passes"] = cc.insufficient and not cc.cited
        else:
            auto["passes"] = bool(auto["retrieval_found_expected"]) and all(mention.values()) \
                and cc.status in ("cited", "cited-with-gaps") and not cc.invalid
        record = {"test": t, "environment": env, **run, "auto_checks": auto,
                  "human_assessment": assessments.get(t["id"], "PENDING: open each cited passage, judge support, "
                                                      "and record the verdict in evals/assessments.json")}
        (out_dir / f"{t['id']}.json").write_text(
            json.dumps(_jsonable(record), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out_dir / f"{t['id']}.md").write_text(card(t, record), encoding="utf-8")
        log(run["answer"])
        log(f"--> auto checks: {'PASS' if auto['passes'] else 'FAIL'}  ({cc.summary()})")
        results.append(record)
    return results


def card(t: dict, r: dict) -> str:
    env, model = r["environment"], r["environment"]["model"]
    cc = r["citation_check"]
    auto = r["auto_checks"]
    lines = [
        f"# Evidence card: {t['id']} ({t['kind']})", "",
        "| | |", "|---|---|",
        f"| Mode | **ask** (standalone, no chat history, no persona) |",
        f"| Execution | **{env['execution']}**; internet reachable during run: **{env['internet_reachable']}** |",
        f"| Model | `{model.get('model')}`, {model.get('parameter_size')} params, {model.get('quantization')}, "
        f"digest `{(model.get('digest') or '')[:12]}` |",
        f"| Runtime | Ollama {model.get('runtime_version')} at {model.get('host')} |",
        f"| Retrieval | {r['retrieval']['method']}, top {r['retrieval']['top_k']}, "
        f"{r['retrieval']['sent_chars']} chars of evidence sent |",
        f"| Response time | {r['timing']['wall_seconds']} s total "
        f"(load {r['timing']['load_seconds']} s, prompt {r['timing']['prompt_tokens']} tok, "
        f"output {r['timing']['output_tokens']} tok) |",
        f"| Loaded model memory | " + (", ".join(f"{m['loaded_size_gb']} GB ({m['in_gpu_vram_gb']} GB in VRAM)"
                                         for m in env["memory"]) or "n/a") + " |",
        f"| Run at | {env['timestamp_utc']} |", "",
        "## Question", "", f"> {t['question']}", "",
        "## Expected (written before the run)", "", f"**Answer:** {t['expected_answer']}", "",
    ]
    for e in t["expected_sources"]:
        lines.append(f"- `{e['file']}` › {e['section']}: “{e['passage']}”")
    if not t["expected_sources"]:
        lines.append("- No source should support an answer.")
    lines += ["", "## Retrieved passages (exactly what Gemma saw)", ""]
    for i, p in enumerate(r["passages"], 1):
        text = p.text if len(p.text) < 700 else p.text[:700] + " …"
        lines += [f"**[S{i}]** `{p.location}` · {p.section} · score {p.score}", "",
                  "```text", text, "```", ""]
    lines += ["## Gemma's answer", "", r["answer"], "",
              "## Automatic checks", "",
              f"- Expected passage retrieved: **{auto['retrieval_found_expected']}** (rank: {auto['expected_ranks']})",
              f"- Mentions expected facts: {auto['mentions_expected_facts']}",
              f"- Citation check: `{cc.summary()}`"]
    if cc.uncited_sentences:
        lines.append("- Uncited sentences: " + " | ".join(f"“{s}”" for s in cc.uncited_sentences))
    if cc.weak_support:
        lines.append("- Weakly supported sentences: " + " | ".join(f"“{s}”" for s in cc.weak_support))
    lines += [f"- **Automatic verdict: {'PASS' if auto['passes'] else 'FAIL'}**", "",
              "## Human assessment", "", r["human_assessment"], ""]
    return "\n".join(lines)


def run_retrieval_eval(h: Harness, questions_path: Path, log=print) -> Path:
    """Step 1 of the evaluation, no model involved: did the expected passages come back?"""
    tests = json.loads(questions_path.read_text(encoding="utf-8"))["tests"]
    k = h.cfg.retrieval.top_k
    lines = ["# Retrieval check (no model)", "",
             f"Method: **{h.cfg.retrieval.method}**, top {k} passages, over {len(h.index.passages)} indexed passages. "
             "Run with `wiki eval --retrieval-only`. This isolates the retrieval tool from Gemma.", ""]
    for t in tests:
        found, method = h.retrieve(t["question"], k)  # same scope as ask: original sources only
        passages = prompts.select_passages(found, h.cfg.retrieval.max_context_chars)
        hits = {e["section"]: _expected_hit(e, passages) for e in t["expected_sources"]}
        ok = all(v is not None for v in hits.values()) if hits else None
        verdict = {True: "PASS: expected passage(s) retrieved", False: "FAIL: expected passage missing",
                   None: "n/a: no passage should answer this; check that nothing retrieved states the answer"}[ok]
        log(f"{t['id']}: {verdict}  ranks={hits}")
        lines += [f"## {t['id']}: {t['question']}", "", f"**{verdict}**. Expected ranks: `{hits}`", "",
                  "| Rank | Location | Section | Score |", "|---:|---|---|---:|"]
        lines += [f"| {i} | `{p.location}` | {p.section} | {p.score} |" for i, p in enumerate(passages, 1)]
        lines.append("")
    out = h.cfg.paths.evidence / "retrieval" / "retrieval-check.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
