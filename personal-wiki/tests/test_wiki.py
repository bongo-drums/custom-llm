"""Harness tests. Run from the project folder:  python -m unittest discover -s tests -v

Retrieval tests use the real sources in vault/raw. Model-dependent tests use
tests/fake_ollama.py (a scripted stand-in for Ollama) in a temporary copy of the project,
so they check the harness's plumbing and guards, not Gemma's answer quality.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fake_ollama import FakeOllama  # noqa: E402
from wiki_cli import citations, cli  # noqa: E402
from wiki_cli.config import load_config  # noqa: E402
from wiki_cli.harness import ChatSession, Harness  # noqa: E402
from wiki_cli.index import Index, Passage, split_section  # noqa: E402
from wiki_cli.ingest import sanitize_title, similar  # noqa: E402
from wiki_cli.llm import ModelUnavailable, OllamaClient  # noqa: E402
from wiki_cli.sources import SourceCatalog, parse_sections  # noqa: E402

QUESTIONS = json.loads((ROOT / "evals" / "questions.json").read_text(encoding="utf-8"))["tests"]
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|[^\]]*)?\]\]")


def temp_project() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="wiki-test-"))
    for name in ("wiki.toml", "instructions", "evals"):
        src = ROOT / name
        (shutil.copytree if src.is_dir() else shutil.copy)(src, tmp / name)
    shutil.copytree(ROOT / "vault" / "raw", tmp / "vault" / "raw")
    (tmp / "vault" / "wiki").mkdir()
    (tmp / "state").mkdir()
    shutil.copy(ROOT / "state" / "source_catalog.json", tmp / "state" / "source_catalog.json")
    return tmp


def run_cli(*argv) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = cli.main(list(argv))
    return code, buf.getvalue()


class SourcesAndRetrieval(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(ROOT / "wiki.toml")
        self.cfg.retrieval.include_wiki_pages = False
        self.index = Index(__import__("wiki_cli.index", fromlist=["build_passages"]).build_passages(self.cfg))

    def test_raw_sources_unchanged(self):
        catalog = SourceCatalog(ROOT / "state" / "source_catalog.json", ROOT / "vault")
        self.assertEqual(catalog.verify(), [])
        self.assertGreaterEqual(len(catalog.entries), 3)

    def test_passage_line_numbers_point_at_original_text(self):
        for p in self.index.passages:
            lines = (ROOT / "vault" / p.file).read_text(encoding="utf-8").splitlines()
            window = "\n".join(lines[p.start_line - 1:p.end_line])
            first_words = re.findall(r"[A-Za-z]{4,}", p.text)[:3]
            for w in first_words:
                self.assertIn(w, window, f"{p.location} does not contain '{w}'")

    def test_sections_ignore_hashes_in_code_fences(self):
        text = "# Title\nintro\n```bash\n# not a heading\n```\n## Real\nbody"
        heads = [s.heading for s in parse_sections(text, "x")]
        self.assertEqual(heads, ["Title", "Real"])

    def test_split_section_keeps_ranges(self):
        text = "\n\n".join(f"paragraph {i} " + "word " * 60 for i in range(6))
        parts = split_section(text, 10, 400)
        self.assertGreater(len(parts), 1)
        self.assertEqual(parts[0][0], 10)
        self.assertEqual(parts[-1][1], 10 + len(text.splitlines()) - 1)

    def test_expected_passages_retrieved_for_answerable_questions(self):
        from wiki_cli.evals import _expected_hit
        for t in QUESTIONS:
            results = self.index.search(t["question"], self.cfg.retrieval.top_k)
            for exp in t["expected_sources"]:
                self.assertIsNotNone(_expected_hit(exp, results),
                                     f"{t['id']}: expected {exp['file']} › {exp['section']} not in top "
                                     f"{self.cfg.retrieval.top_k}: {[r.location for r in results]}")


class Titles(unittest.TestCase):
    def test_sanitize(self):
        self.assertEqual(sanitize_title("row level security"), "Row Level Security")
        self.assertEqual(sanitize_title("Replay Memory"), "Replay Memory")
        self.assertIsNone(sanitize_title("class4-gpu-parallel-training-visual--task-1--c8d92e24fd"))
        self.assertIsNone(sanitize_title("This is a long sentence about what the project did overall"))
        self.assertIsNone(sanitize_title("2026-09-01 notes"))
        self.assertIsNone(sanitize_title("Why did it fail?"))
        self.assertEqual(sanitize_title("Next.js: App Router"), "Next.js App Router")
        self.assertEqual(sanitize_title("Four-row Eval Comparison (all"), "Four-row Eval Comparison")
        self.assertEqual(sanitize_title("My Hyperparameters"), "Hyperparameters")
        self.assertIsNone(sanitize_title("Table of Contents"))
        self.assertIsNone(sanitize_title("Screenshots"))

    def test_similar_titles_merge(self):
        self.assertTrue(similar("Row Level Security", "Postgres Row Level Security"))
        self.assertTrue(similar("Learning Rate", "learning rates"))
        self.assertFalse(similar("Replay Memory", "Replay Buffer Size Choice"))


class Citations(unittest.TestCase):
    def setUp(self):
        mk = lambda t: Passage("id", "raw", "raw/x.md", "src", "S", "S", 1, 2, t)
        self.passages = [mk("| Exploration | **0.10** | Half the notebook's 0.20"), mk("Learning rate 0.0001")]

    def test_cited_answer(self):
        r = citations.check("The exploration rate was 0.10 [S1].", self.passages)
        self.assertEqual(r.status, "cited")

    def test_invalid_citation(self):
        self.assertEqual(citations.check("It was 0.10 [S7].", self.passages).status, "invalid")

    def test_number_not_in_cited_passage(self):
        r = citations.check("The exploration rate was 0.35 [S1].", self.passages)
        self.assertIn("0.35", r.unsupported_numbers)
        self.assertEqual(r.status, "cited-with-gaps")

    def test_insufficient(self):
        r = citations.check("INSUFFICIENT EVIDENCE: no grade is mentioned.", self.passages)
        self.assertEqual(r.status, "insufficient")


class WithFakeModel(unittest.TestCase):
    """End-to-end through the real CLI and HTTP client, with the scripted stand-in for Ollama."""

    def setUp(self):
        self.tmp = temp_project()
        self.fake = FakeOllama().__enter__()
        self.base = ["--config", str(self.tmp / "wiki.toml"), "--host", self.fake.url]

    def tearDown(self):
        self.fake.__exit__(None, None, None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def wiki_files(self) -> list[Path]:
        return sorted((self.tmp / "vault" / "wiki").rglob("*.md"))

    def assert_links_resolve(self):
        vault = self.tmp / "vault"
        stems = {p.stem: p for p in vault.rglob("*.md")}
        for f in self.wiki_files() + [vault / "index.md"]:
            for target, heading in WIKILINK.findall(f.read_text(encoding="utf-8")):
                self.assertIn(target, stems, f"broken link [[{target}]] in {f.name}")
                if heading:
                    headings = [s.heading for s in parse_sections(stems[target].read_text(encoding="utf-8"), target)]
                    self.assertIn(heading, headings, f"missing heading [[{target}#{heading}]] in {f.name}")

    def test_ingest_builds_readable_linked_vault_and_reingest_has_no_duplicates(self):
        code, output = run_cli(*self.base, "ingest", str(self.tmp / "vault" / "raw"))
        self.assertEqual(code, 0, output)
        files = self.wiki_files()
        self.assertGreaterEqual(len(files), 6)
        folders = {f.parent.name for f in files}
        self.assertLessEqual(folders, {"Projects", "Concepts", "Tools"})
        for f in files:
            words = f.stem.split()
            self.assertLessEqual(len(words), 6, f.name)
            self.assertNotRegex(f.stem, r"[0-9a-f]{8}|--|_")
            h1 = next(l for l in f.read_text(encoding="utf-8").splitlines() if l.startswith("# "))
            self.assertEqual(h1[2:], f.stem, "H1 must match the filename")
            self.assertIn("## Sources", f.read_text(encoding="utf-8"))
        text = "\n".join(f.read_text(encoding="utf-8") for f in files)
        self.assertNotIn("987654", text, "invented number should be dropped")
        self.assertNotIn("Nonexistent Note", text, "link to missing note should be dropped")
        index = (self.tmp / "vault" / "index.md").read_text(encoding="utf-8")
        for f in files:
            self.assertIn(f"[[{f.stem}]]", index)
        self.assert_links_resolve()

        # mark one page reviewed and edit it by hand: re-ingest must leave it alone
        reviewed = next(f for f in files if f.parent.name == "Concepts")
        edited = reviewed.read_text(encoding="utf-8").replace("reviewed: false", "reviewed: true") + "\nMy correction.\n"
        reviewed.write_text(edited, encoding="utf-8")

        names_before = [f.relative_to(self.tmp) for f in files]
        code, output = run_cli(*self.base, "ingest", str(self.tmp / "vault" / "raw" / "ms-pacman-README.md"))
        self.assertEqual(code, 0, output)
        self.assertEqual([f.relative_to(self.tmp) for f in self.wiki_files()], names_before, "re-ingest changed page set")
        self.assertEqual(reviewed.read_text(encoding="utf-8"), edited)
        self.assert_links_resolve()
        self.assertEqual(SourceCatalog(self.tmp / "state" / "source_catalog.json", self.tmp / "vault").verify(), [])

    def test_ask_is_standalone_and_saves_evidence(self):
        cfg = load_config(self.tmp / "wiki.toml")
        cfg.model.host = self.fake.url
        h = Harness(cfg)
        chat = ChatSession(h)
        chat.send("By the way, I got an A+ on the Pac-Man assignment grade.")
        run = h.ask("What grade did I receive on the Ms. Pac-Man assignment?")
        prompt_text = json.dumps(run["prompt"])
        self.assertNotIn("A+", prompt_text, "chat claims must not reach ask mode")
        self.assertNotIn("Scout", prompt_text, "ask must not load the chat persona")
        self.assertIn("Research rules", prompt_text)
        self.assertEqual(run["citation_check"].status, "insufficient")

        code, output = run_cli(*self.base, "ask", "What exploration rate did I use for Ms. Pac-Man?")
        self.assertEqual(code, 0, output)
        self.assertIn("[S1] cited", output)
        self.assertTrue(list((self.tmp / "evidence" / "ask").glob("ask-*.json")))

    def test_chat_routing_and_follow_up(self):
        cfg = load_config(self.tmp / "wiki.toml")
        cfg.model.host = self.fake.url
        s = ChatSession(Harness(cfg))
        t1 = s.send("what can we do?")
        self.assertFalse(t1["decision"]["retrieve"])
        self.assertNotIn("INSUFFICIENT", t1["reply"])
        s.send("Draft a short study plan for my three projects")
        n_before = len(self.fake.requests)
        t3 = s.send("make that shorter")
        self.assertFalse(t3["decision"]["retrieve"])
        self.assertEqual(len(self.fake.requests) - n_before, 1, "an edit follow-up should skip the router call")
        sent = self.fake.requests[-1]["messages"]
        self.assertIn("Draft a short study plan", json.dumps(sent), "follow-up must include the conversation")
        t4 = s.send("What exploration rate did my Pac-Man agent use?")
        self.assertTrue(t4["decision"]["retrieve"])
        self.assertTrue(t4["passages"])
        path = s.save_transcript("test-transcript")
        self.assertTrue(path.exists() and path.with_suffix(".md").exists())

    def test_chat_script_mode(self):
        script = self.tmp / "script.txt"
        script.write_text("what can you help me with?\nmake that shorter\n/exit\n", encoding="utf-8")
        code, output = run_cli(*self.base, "chat", "--script", str(script))
        self.assertEqual(code, 0, output)
        self.assertIn("no notes lookup", output)
        self.assertTrue(list((self.tmp / "evidence" / "chat").glob("*.md")))

    def test_eval_writes_four_cards(self):
        code, output = run_cli(*self.base, "ingest")
        self.assertEqual(code, 0, output)
        code, output = run_cli(*self.base, "eval")
        self.assertEqual(code, 0, output)
        cards = sorted((self.tmp / "evidence" / "ask").glob("test-*.md"))
        self.assertEqual([c.stem for c in cards], ["test-1", "test-2", "test-3", "test-4"])
        self.assertIn("Retrieved passages", cards[0].read_text(encoding="utf-8"))
        for card in (self.tmp / "evidence" / "ask").glob("test-*.json"):
            kinds = {p["kind"] for p in json.loads(card.read_text(encoding="utf-8"))["passages"]}
            self.assertEqual(kinds, {"raw"}, f"{card.name}: ask must cite original sources only, even after ingest")


class Errors(unittest.TestCase):
    def test_runtime_down_gives_actionable_error(self):
        client = OllamaClient(load_config(ROOT / "wiki.toml").model)
        client.host = "http://127.0.0.1:9"
        with self.assertRaises(ModelUnavailable) as ctx:
            client.ensure_ready()
        self.assertIn("ollama serve", str(ctx.exception))

    def test_missing_model_gives_pull_command(self):
        with FakeOllama(models=["something-else:latest"]) as fake:
            cfg = load_config(ROOT / "wiki.toml")
            cfg.model.host = fake.url
            with self.assertRaises(ModelUnavailable) as ctx:
                OllamaClient(cfg.model).ensure_ready()
            self.assertIn(f"ollama pull {cfg.model.name}", str(ctx.exception))

    def test_search_works_without_model_and_ask_reports_it(self):
        tmp = temp_project()
        try:
            base = ["--config", str(tmp / "wiki.toml"), "--host", "http://127.0.0.1:9"]
            code, output = run_cli(*base, "search", "row level security")
            self.assertEqual(code, 0, output)
            self.assertIn("networking-tracker-README.md", output)
            code, output = run_cli(*base, "ask", "anything")
            self.assertEqual(code, 2)
            self.assertIn("Cannot reach the local model runtime", output)
            code, output = run_cli(*base, "ingest", str(tmp / "nope"))
            self.assertEqual(code, 2)
            self.assertIn("No such file or folder", output)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
