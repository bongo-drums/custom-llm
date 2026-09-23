"""`wiki` command-line interface: parse the command, pick the mode, print results, save evidence."""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
import time
from pathlib import Path

from .config import load_config
from .harness import CAPABILITIES, ChatSession, Harness, now_stamp, slug
from .llm import ModelUnavailable, internet_reachable

DESCRIPTION = """\
Personal wiki CLI: your notes + a local Gemma model (via Ollama) + your own harness.

Commands (modes):
  ingest   read sources in vault/raw, have local Gemma write linked notes in vault/wiki, update vault/index.md
  search   show original matching passages and file paths. No model is used; works with Ollama stopped
  ask      one standalone factual answer from retrieved passages, with [S#] citations or INSUFFICIENT EVIDENCE
  chat     personal assistant "Scout": conversation memory; looks in the notes only when a message needs them
  eval     run the four fixed ask-mode tests in evals/questions.json and write evidence cards
  status   show model/runtime identity, quantization, loaded memory, index size, internet reachability
  help     show this help (same as --help)
"""

EPILOG = """\
Configuration: wiki.toml (model name, Ollama host, context size, retrieval method, paths).
Required inputs: Ollama running locally (`ollama serve`) with the model pulled (`ollama pull gemma4:e2b`),
and at least one .md/.txt source in vault/raw/. `search` needs neither Ollama nor the model.

Examples:
  wiki ingest vault/raw
  wiki search "row level security policy"
  wiki ask "Where is the workshop?" --mode local
  wiki chat
  wiki eval
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wiki", description=DESCRIPTION, epilog=EPILOG,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", type=Path, help="path to wiki.toml (default: next to the wiki_cli package)")
    p.add_argument("--model", help="override the Gemma model tag, e.g. gemma4:e4b")
    p.add_argument("--host", help="override the Ollama address (default http://localhost:11434)")
    sub = p.add_subparsers(dest="command", metavar="<command>")

    s = sub.add_parser("ingest", help="turn raw sources into linked wiki notes (uses local Gemma)")
    s.add_argument("path", type=Path, nargs="?", default=None, help="a raw file or folder (default: vault/raw)")
    s.add_argument("--relink-all", action="store_true", help="re-run the related-notes step for every page")

    s = sub.add_parser("search", help="show matching original passages (no model)")
    s.add_argument("query")
    s.add_argument("-k", type=int, default=5, help="number of passages (default 5)")
    s.add_argument("--full", action="store_true", help="print whole passages instead of previews")
    s.add_argument("--include-wiki", action="store_true",
                   help="also search generated vault/wiki pages (default: original sources only)")
    s.add_argument("--save", action="store_true", help="save the results under evidence/search/")

    s = sub.add_parser("ask", help="standalone factual answer with citations")
    s.add_argument("question")
    s.add_argument("--mode", choices=["local", "online"], default="local",
                   help="where the model runs; only local is implemented (default local)")
    s.add_argument("--no-save", action="store_true", help="do not write an evidence record")

    s = sub.add_parser("chat", help="personal assistant with conversation memory")
    s.add_argument("--script", type=Path, help="read user messages from a file (one per line) instead of the keyboard")
    s.add_argument("--mode", choices=["local", "online"], default="local")

    s = sub.add_parser("eval", help="run the four ask-mode tests and write evidence cards")
    s.add_argument("--questions", type=Path, default=None, help="default: evals/questions.json")
    s.add_argument("--only", nargs="*", help="test ids to run, e.g. test-1 test-4")
    s.add_argument("--retrieval-only", action="store_true",
                   help="check only whether the expected passages are retrieved (no model needed)")

    sub.add_parser("status", help="model/runtime identity, memory, index, network")
    sub.add_parser("help", help="show this help")
    return p


# ---------------------------------------------------------------- output helpers

def out(text: str = "") -> None:
    print(text, flush=True)


def dim(text: str) -> str:
    return f"\033[2m{text}\033[0m" if sys.stdout.isatty() else text


def rule(title: str = "") -> None:
    out(f"── {title} " + "─" * max(0, 68 - len(title)) if title else "─" * 72)


def banner(h: Harness, mode: str) -> None:
    out(dim(f"[{mode} · model {h.cfg.model.name} via Ollama at {h.cfg.model.host} · execution: local]"))


def print_passages(passages, full: bool = False) -> None:
    for i, p in enumerate(passages, 1):
        out(f"[S{i}] {p.location}   score {p.score}   ({p.kind})")
        out(f"     section: {p.section}")
        out(f"     obsidian: {p.obsidian_link}")
        body = p.text if full else (p.text[:420] + (" …" if len(p.text) > 420 else ""))
        out(textwrap.indent(body, "     │ "))
        out()


def reject_online(mode: str) -> None:
    if mode == "online":
        raise SystemExit("error: online mode is not configured in this project. Local mode is the required, "
                         "default path: omit --mode or use --mode local.")


# ---------------------------------------------------------------- commands

def cmd_ingest(h: Harness, args) -> int:
    from .ingest import run_ingest
    from .sources import iter_raw_files

    target = args.path or h.cfg.paths.raw
    files = iter_raw_files(target.resolve())
    raw_root = h.cfg.paths.raw
    for f in files:
        if raw_root not in f.resolve().parents:
            raise SystemExit(f"error: {f} is not inside {raw_root}. Copy originals into vault/raw/ first "
                             "(they are kept unchanged there).")
    banner(h, "ingest")
    h.client.ensure_ready()
    out(f"Ingesting {len(files)} source(s) with {h.cfg.model.name} …")
    report = run_ingest(h.cfg, h.client, files, log=out, relink_all=args.relink_all)
    rule("ingest summary")
    out(f"pages: {report['pages_before']} -> {report['pages_after']}   time: {report['seconds']}s   "
        f"model calls: {len(report['calls'])}")
    out(f"created: {', '.join(report['created']) or '-'}")
    out(f"updated: {', '.join(report['updated']) or '-'}")
    out(f"removed: {', '.join(report['removed']) or '-'}")
    if report["skipped_reviewed"]:
        out(f"left alone (reviewed: true): {', '.join(report['skipped_reviewed'])}")
    if report["dropped_topics"] or report["dropped_bullets"] or report["dropped_links"]:
        out(f"dropped by checks: {len(report['dropped_topics'])} topics, {len(report['dropped_bullets'])} bullets, "
            f"{len(report['dropped_links'])} links (details in the saved report)")
    report["environment"] = h.environment()
    path = h.save_record(report, "ingest", f"ingest-{now_stamp()}")
    out(f"index: {h.cfg.paths.index_md}   report: {path}")
    return 0


def cmd_search(h: Harness, args) -> int:
    res = h.search(args.query, args.k, args.include_wiki)
    out(dim(f"[search · retrieval only, no model · {res['method']} · scope {'+'.join(res['scope'])} · "
            f"{res['seconds']*1000:.0f} ms]"))
    if not res["passages"]:
        out("No matching passages. Try other words, or check that sources exist in vault/raw/.")
        return 1
    print_passages(res["passages"], args.full)
    if args.save:
        path = h.save_record(res, "search", f"search-{slug(args.query)}")
        out(dim(f"saved: {path}"))
    return 0


def cmd_ask(h: Harness, args) -> int:
    reject_online(args.mode)
    banner(h, "ask")
    rule("answer")
    streamed = []
    run = h.ask(args.question, on_token=lambda t: (streamed.append(t), print(t, end="", flush=True)))
    out()
    rule("sources shown to Gemma")
    for i, p in enumerate(run["passages"], 1):
        mark = "cited" if i in run["citation_check"].cited else "     "
        out(f"[S{i}] {mark}  {p.location}  ·  {p.section}")
    rule("checks")
    out(run["citation_check"].summary())
    for s in run["citation_check"].uncited_sentences:
        out(f"  uncited: {s}")
    out(dim(f"{run['timing']['wall_seconds']}s · prompt {run['timing']['prompt_tokens']} tok · "
            f"output {run['timing']['output_tokens']} tok"))
    if not args.no_save:
        run["environment"] = h.environment()
        path = h.save_record(run, "ask", f"ask-{now_stamp()}-{slug(args.question)}")
        out(dim(f"saved: {path}"))
    return 0


def cmd_chat(h: Harness, args) -> int:
    reject_online(args.mode)
    h.client.ensure_ready()
    session = ChatSession(h)
    banner(h, "chat")
    out("Scout here — your local study-and-projects assistant. Type /help for commands, /exit to quit.\n")

    if args.script:
        lines = [l.rstrip("\n") for l in args.script.read_text(encoding="utf-8").splitlines()]
        messages = iter([l for l in lines if l.strip() and not l.startswith("#")])
    else:
        messages = None

    while True:
        if messages is not None:
            try:
                msg = next(messages)
            except StopIteration:
                break
            out(f"you> {msg}")
        else:
            try:
                msg = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                out()
                break
        if not msg:
            continue
        cmd = msg.split()[0].lower()
        if cmd in ("/exit", "/quit"):
            break
        if cmd == "/help":
            out(CAPABILITIES + "\n")
            continue
        if cmd == "/reset":
            session.reset()
            out(dim("(conversation cleared)\n"))
            continue
        if cmd == "/sources":
            print_passages(session.last_passages) if session.last_passages else out("(no notes were used last turn)\n")
            continue
        if cmd == "/save":
            path = session.save_draft(h.cfg.paths.drafts)
            out(dim(f"(saved draft to {path} — kept out of the vault and never used as evidence)\n") if path
                else "(nothing to save yet)\n")
            continue

        def on_decision(d):
            out(dim(f"  [harness: {'searching notes for “' + d.query + '”' if d.retrieve else 'no notes lookup'}"
                    f" — {d.reason}]"))
        print("scout> ", end="", flush=True)
        try:
            turn = session.send(msg, on_token=lambda t: print(t, end="", flush=True), on_decision=on_decision)
        except ModelUnavailable as e:
            out(f"\n[error] {e}\n")
            continue
        out()
        if turn["passages"]:
            out(dim("  sources: " + "; ".join(f"[{p['tag']}] {p['location']}" for p in turn["passages"])))
            out(dim(f"  citation check: {turn['citation_check']['status']}"))
        out(dim(f"  ({turn['timing']['wall_seconds']}s)") + "\n")

    if session.log:
        path = session.save_transcript()
        out(dim(f"transcript saved: {path} (+ .md)"))
    return 0


def cmd_eval(h: Harness, args) -> int:
    from .evals import run_eval, run_retrieval_eval
    qpath = args.questions or (h.cfg.paths.root / "evals" / "questions.json")
    if args.retrieval_only:
        out(dim("[eval · retrieval only, no model]"))
        out(f"report: {run_retrieval_eval(h, qpath, log=out)}")
        return 0
    banner(h, "eval (ask mode)")
    h.client.ensure_ready()
    results = run_eval(h, qpath, args.only, log=out)
    rule("summary")
    for r in results:
        a = r["auto_checks"]
        out(f"{r['test']['id']}: {'PASS' if a['passes'] else 'FAIL'}   retrieval={a['retrieval_found_expected']}  "
            f"citations={a['citation_status']}  {r['timing']['wall_seconds']}s")
    out(f"cards: {h.cfg.paths.evidence / 'ask'}")
    return 0


def cmd_status(h: Harness, args) -> int:
    from .sources import SourceCatalog
    cfg = h.cfg
    out(f"config:     {cfg.paths.root / 'wiki.toml'}")
    out(f"vault:      {cfg.paths.vault}")
    catalog = SourceCatalog(cfg.paths.state / "source_catalog.json", cfg.paths.vault)
    problems = catalog.verify()
    out(f"sources:    {len(catalog.entries)} catalogued; "
        + ("all unchanged (SHA-256 match)" if not problems else "; ".join(problems)))
    pages = list(cfg.paths.wiki.rglob("*.md")) if cfg.paths.wiki.exists() else []
    out(f"wiki pages: {len(pages)}")
    t = time.perf_counter()
    idx = h.index
    out(f"index:      {len(idx.passages)} passages ({'rebuilt' if h.index_rebuilt else 'cached'}, "
        f"{(time.perf_counter()-t)*1000:.0f} ms), method {cfg.retrieval.method}")
    out(f"internet:   {'reachable' if internet_reachable() else 'NOT reachable (offline)'}")
    ident = h.client.identity()
    if "error" in ident:
        out(f"model:      {cfg.model.name} — UNAVAILABLE: {ident['error']}")
        out("            (search still works; ask/chat/ingest need the local model)")
        return 1
    out(f"runtime:    Ollama {ident.get('runtime_version')} at {ident.get('host')}")
    out(f"model:      {ident.get('model')}  family={ident.get('family')}  params={ident.get('parameter_size')}  "
        f"quant={ident.get('quantization')}  file={ident.get('file_size_gb')} GB  digest={str(ident.get('digest'))[:12]}")
    mem = h.client.memory()
    out("loaded:     " + (", ".join(f"{m['model']} {m['loaded_size_gb']} GB total, {m['in_gpu_vram_gb']} GB in VRAM, "
                                    f"ctx {m['context_length']}" for m in mem) or "no model loaded right now"))
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in (None, "help"):
        parser.print_help()
        return 0
    try:
        cfg = load_config(args.config)
        if args.model:
            cfg.model.name = args.model
        if args.host:
            cfg.model.host = args.host
        h = Harness(cfg)
        handler = {"ingest": cmd_ingest, "search": cmd_search, "ask": cmd_ask, "chat": cmd_chat,
                   "eval": cmd_eval, "status": cmd_status}[args.command]
        return handler(h, args)
    except ModelUnavailable as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:  # output piped into e.g. `head`
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(main())
