"""Local Gemma client: a thin wrapper over Ollama's HTTP API on localhost.

The model never reads files on its own. Every call here sends exactly the messages
the harness assembled, and returns the text plus timing numbers Ollama reports.
Only the Python standard library is used, so there is nothing to install for this layer.
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

from .config import ModelConfig


class ModelUnavailable(RuntimeError):
    """Raised with a message that tells the user exactly how to fix the problem."""


@dataclass
class ChatResult:
    text: str
    model: str
    seconds: float
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    raw_stats: dict = field(default_factory=dict)

    def stats(self) -> dict:
        return {
            "model": self.model,
            "wall_seconds": round(self.seconds, 2),
            "prompt_tokens": self.prompt_tokens,
            "output_tokens": self.output_tokens,
            "load_seconds": _ns_to_s(self.raw_stats.get("load_duration")),
            "prompt_eval_seconds": _ns_to_s(self.raw_stats.get("prompt_eval_duration")),
            "generation_seconds": _ns_to_s(self.raw_stats.get("eval_duration")),
        }


def _ns_to_s(value):
    return round(value / 1e9, 2) if isinstance(value, (int, float)) else None


class OllamaClient:
    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg
        self.host = cfg.host.rstrip("/")

    # ---------- low-level HTTP ----------
    def _request(self, path: str, payload: dict | None = None, timeout: float | None = None):
        url = f"{self.host}{path}"
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            url, data=data, method="POST" if data else "GET",
            headers={"Content-Type": "application/json"},
        )
        try:
            return urllib.request.urlopen(req, timeout=timeout or self.cfg.timeout_seconds)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code == 404 and "not found" in body.lower():
                raise ModelUnavailable(
                    f"Model not found in Ollama: {body.strip()}\n"
                    f"  While online, download it once:  ollama pull {self.cfg.name}\n"
                    f"  Then check it is listed by:      ollama list"
                ) from None
            raise ModelUnavailable(f"Ollama returned HTTP {e.code} for {path}: {body.strip()}") from None
        except (urllib.error.URLError, ConnectionError, socket.timeout, TimeoutError) as e:
            reason = getattr(e, "reason", e)
            raise ModelUnavailable(
                f"Cannot reach the local model runtime at {self.host} ({reason}).\n"
                f"  Start it with:  ollama serve   (or open the Ollama app)\n"
                f"  `wiki search` still works without the model."
            ) from None

    def _get_json(self, path: str, payload: dict | None = None, timeout: float | None = None) -> dict:
        with self._request(path, payload, timeout) as resp:
            return json.loads(resp.read().decode())

    # ---------- runtime / model identity ----------
    def version(self) -> str:
        return self._get_json("/api/version", timeout=5).get("version", "unknown")

    def list_models(self) -> list[str]:
        return [m["name"] for m in self._get_json("/api/tags", timeout=5).get("models", [])]

    def show(self, model: str | None = None) -> dict:
        return self._get_json("/api/show", {"model": model or self.cfg.name}, timeout=30)

    def running(self) -> list[dict]:
        """Models currently loaded in memory, with their RAM/VRAM footprint."""
        return self._get_json("/api/ps", timeout=5).get("models", [])

    def ensure_ready(self, model: str | None = None) -> None:
        model = model or self.cfg.name
        names = self.list_models()
        wanted = {model, model if ":" in model else f"{model}:latest"}
        if not wanted & set(names):
            listed = ", ".join(names) or "(none)"
            raise ModelUnavailable(
                f"Model '{model}' is not downloaded. Installed models: {listed}\n"
                f"  While online, run:  ollama pull {model}\n"
                f"  Or pick an installed one:  wiki --model <name> ...  (or edit wiki.toml)"
            )

    def identity(self) -> dict:
        """Exact model/runtime identity for evidence records."""
        info = {"backend": "ollama (local)", "host": self.host, "model": self.cfg.name}
        try:
            info["runtime_version"] = self.version()
            shown = self.show()
            details = shown.get("details", {})
            info.update({
                "family": details.get("family"),
                "parameter_size": details.get("parameter_size"),
                "quantization": details.get("quantization_level"),
                "format": details.get("format"),
            })
            for m in self._get_json("/api/tags", timeout=5).get("models", []):
                if m["name"] in (self.cfg.name, f"{self.cfg.name}:latest"):
                    info["digest"] = m.get("digest")
                    info["file_size_gb"] = round(m.get("size", 0) / 1e9, 2)
        except ModelUnavailable as e:
            info["error"] = str(e).splitlines()[0]
        return info

    def memory(self) -> list[dict]:
        out = []
        try:
            for m in self.running():
                out.append({
                    "model": m.get("name"),
                    "loaded_size_gb": round(m.get("size", 0) / 1e9, 2),
                    "in_gpu_vram_gb": round(m.get("size_vram", 0) / 1e9, 2),
                    "context_length": m.get("context_length"),
                })
        except ModelUnavailable:
            pass
        return out

    # ---------- generation ----------
    def chat(
        self,
        messages: list[dict],
        *,
        json_schema: dict | None = None,
        on_token: Callable[[str], None] | None = None,
        temperature: float | None = None,
        model: str | None = None,
    ) -> ChatResult:
        model = model or self.cfg.name
        payload = {
            "model": model,
            "messages": messages,
            "stream": on_token is not None,
            "keep_alive": self.cfg.keep_alive,
            "options": {
                "temperature": self.cfg.temperature if temperature is None else temperature,
                "seed": self.cfg.seed,
                "num_ctx": self.cfg.num_ctx,
            },
        }
        if json_schema is not None:
            payload["format"] = json_schema  # Ollama structured output: constrains decoding to this schema

        start = time.perf_counter()
        pieces: list[str] = []
        final: dict = {}
        with self._request("/api/chat", payload) as resp:
            if on_token is None:
                final = json.loads(resp.read().decode())
                pieces.append(final.get("message", {}).get("content", ""))
            else:
                for line in resp:
                    if not line.strip():
                        continue
                    chunk = json.loads(line.decode())
                    if "error" in chunk:
                        raise ModelUnavailable(f"Ollama error: {chunk['error']}")
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        pieces.append(token)
                        on_token(token)
                    if chunk.get("done"):
                        final = chunk
        if "error" in final:
            raise ModelUnavailable(f"Ollama error: {final['error']}")
        return ChatResult(
            text="".join(pieces).strip(),
            model=model,
            seconds=time.perf_counter() - start,
            prompt_tokens=final.get("prompt_eval_count"),
            output_tokens=final.get("eval_count"),
            raw_stats={k: v for k, v in final.items() if k.endswith("_duration") or k.endswith("_count")},
        )

    def chat_json(self, messages: list[dict], schema: dict, retries: int = 2) -> tuple[dict, ChatResult]:
        """Structured call: decoding is schema-constrained, and we still validate and retry."""
        last_error = None
        for attempt in range(retries + 1):
            result = self.chat(messages, json_schema=schema, temperature=0 if attempt == 0 else 0.4)
            try:
                return _parse_json(result.text), result
            except ValueError as e:
                last_error = e
        raise ModelUnavailable(f"Gemma did not return valid JSON after {retries + 1} tries: {last_error}")

    def embed(self, texts: list[str], model: str) -> list[list[float]]:
        data = self._get_json("/api/embed", {"model": model, "input": texts, "keep_alive": self.cfg.keep_alive})
        return data["embeddings"]


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("no JSON object in reply")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(str(e)) from None


def internet_reachable(timeout: float = 2.0) -> bool:
    """Evidence helper: can this machine open a TCP connection to the public internet?

    Used only to *record* whether a run happened offline. Nothing is sent.
    """
    for host in (("1.1.1.1", 443), ("8.8.8.8", 53)):
        try:
            with socket.create_connection(host, timeout=timeout):
                return True
        except OSError:
            continue
    return False
