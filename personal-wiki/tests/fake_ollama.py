"""TEST DOUBLE ONLY: a tiny HTTP server that imitates Ollama's API with scripted replies.

It lets the unit tests exercise the real HTTP client, ingestion pipeline, routing and
CLI without Gemma weights. Nothing it produces is evidence of model quality; all
submitted evidence comes from real local Gemma runs (see evidence/).

It deliberately returns some bad output (a hash-like title, a sentence title, an
invented number, a link to a missing note) so the harness's guards are tested.
"""

from __future__ import annotations

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL = "gemma4:e2b"


class FakeOllama:
    def __init__(self, models=(MODEL, "embeddinggemma:latest")):
        self.models = list(models)
        self.requests: list[dict] = []
        handler = self._make_handler()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()

    # ------------------------------------------------------------------
    def _make_handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, obj, status=200):
                body = json.dumps(obj).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/api/version":
                    return self._send({"version": "0.0.0-fake"})
                if self.path == "/api/tags":
                    return self._send({"models": [{"name": m, "size": 2_000_000_000, "digest": "f" * 64}
                                                  for m in fake.models]})
                if self.path == "/api/ps":
                    return self._send({"models": [{"name": MODEL, "size": 3_100_000_000,
                                                   "size_vram": 3_100_000_000, "context_length": 8192}]})
                self._send({"error": "not found"}, 404)

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                fake.requests.append({"path": self.path, **payload})
                if self.path == "/api/show":
                    return self._send({"details": {"family": "gemma4", "parameter_size": "5.1B",
                                                   "quantization_level": "Q4_K_M", "format": "gguf"}})
                if self.path == "/api/embed":
                    return self._send({"embeddings": [_embed(t) for t in payload["input"]]})
                if self.path != "/api/chat":
                    return self._send({"error": "not found"}, 404)
                if payload["model"] not in fake.models:
                    return self._send({"error": f"model '{payload['model']}' not found"}, 404)
                text = reply(payload)
                stats = {"done": True, "prompt_eval_count": 100, "eval_count": 20,
                         "total_duration": 1_000_000_000, "load_duration": 100_000_000,
                         "prompt_eval_duration": 300_000_000, "eval_duration": 600_000_000}
                if payload.get("stream"):
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-ndjson")
                    self.end_headers()
                    for word in re.findall(r"\S+\s*", text):
                        self.wfile.write((json.dumps({"message": {"content": word}, "done": False}) + "\n").encode())
                    self.wfile.write((json.dumps({"message": {"content": ""}, **stats}) + "\n").encode())
                    return
                self._send({"message": {"role": "assistant", "content": text}, **stats})

        return Handler


def _embed(text: str) -> list[float]:
    vec = [0.0] * 16
    for w in re.findall(r"[a-z]+", text.lower()):
        vec[hash(w) % 16] += 1.0
    return vec


def reply(payload: dict) -> str:
    msgs = payload["messages"]
    system = msgs[0]["content"] if msgs[0]["role"] == "system" else ""
    user = msgs[-1]["content"]
    schema = payload.get("format")
    props = schema.get("properties", {}) if isinstance(schema, dict) else {}

    if "topics" in props:                      # ingest planning
        labels = re.findall(r"^- (.+?): ", user, re.M)
        topics = []
        from wiki_cli.ingest import sanitize_title
        for label in labels[1:]:
            name = re.sub(r"^\d+\.\s*", "", label.split(" > ")[-1])
            name = " ".join(name.split()[:4])
            if sanitize_title(name) and len(topics) < 3:
                topics.append({"title": name, "category": "Concepts", "sections": [label]})
        topics.append({"title": "class4-task-1--c8d92e24fd", "category": "Concepts", "sections": [labels[0]]})
        topics.append({"title": "This is a long sentence about what the project did overall", "category": "Tools",
                       "sections": [labels[0]]})
        return json.dumps({"project_summary": "A class project. It is described in the source.",
                           "key_facts": [{"text": _first_line(user), "section": labels[0] if labels else ""}],
                           "topics": topics})
    if "details" in props:                     # ingest note writing
        blocks = re.findall(r"### SECTION: (.+)\n([\s\S]*?)(?=\n### SECTION: |\n\nReturn summary)", user)
        details = []
        for label, body in blocks:
            sentence = _first_line(body)
            if sentence:
                details.append({"text": sentence, "section": label})
        details.append({"text": "The agent scored 987654 points in a secret run.", "section": blocks[0][0] if blocks else ""})
        return json.dumps({"summary": "A topic from the project. It appears in the source.", "details": details})
    if "links" in props:                       # ingest linking
        cands = re.findall(r"^- (.+?): ", user, re.M)
        links = [{"title": c, "reason": "Shares the same design concern."} for c in cands[:2]]
        links.append({"title": "Nonexistent Note", "reason": "made up"})
        return json.dumps({"links": links})
    if "needs_notes" in props:                 # chat router
        msg = user.split("New message:", 1)[-1].lower()
        needs = any(k in msg for k in ("pac-man", "exploration", "contacts", "nanogpt", "my project"))
        return json.dumps({"needs_notes": needs, "search_query": msg.strip() if needs else ""})
    if props.get("summary") and len(props) == 1:
        return json.dumps({"summary": "Merged summary of the topic."})

    if "Research rules" in system:              # ask mode
        question = user.split("QUESTION\n========\n", 1)[-1].split("\n")[0].lower()
        evidence = user.split("QUESTION", 1)[0].lower()
        if "grade" in question and "grade" not in evidence.replace("grader", ""):
            return "INSUFFICIENT EVIDENCE: the wiki does not say what grade was received."
        if "exploration" in question:
            return "The exploration rate was 0.10 [S1]."
        return "The notes answer this [S1]."
    # chat mode
    last_assistant = next((m["content"] for m in reversed(msgs) if m["role"] == "assistant"), "")
    if "shorter" in user.lower() and last_assistant:
        return "Shorter: " + last_assistant[:40]
    if "NOTES FROM THE WIKI" in user:
        return "From your notes: exploration was 0.10 [S1]."
    return "I can help you brainstorm, draft, and look things up in your notes. Suggestion: start with /notes."


def _first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if len(line) > 40 and not line.startswith(("#", "|", "```", "<", "!", "-")):
            return line[:200]
    return ""
