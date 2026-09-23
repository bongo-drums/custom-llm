"""Load wiki.toml and resolve paths relative to the project root."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class ModelConfig:
    backend: str = "ollama"
    host: str = "http://localhost:11434"
    name: str = "gemma4:e2b"
    temperature: float = 0.2
    seed: int = 42
    num_ctx: int = 8192
    timeout_seconds: int = 600
    keep_alive: str = "10m"


@dataclass
class RetrievalConfig:
    method: str = "bm25"
    embedding_model: str = "embeddinggemma"
    top_k: int = 6
    max_context_chars: int = 6000
    chunk_chars: int = 1200
    include_wiki_pages: bool = True


@dataclass
class ChatConfig:
    history_turns: int = 6
    chat_top_k: int = 4


@dataclass
class Paths:
    root: Path
    vault: Path
    raw: Path
    wiki: Path
    index_md: Path
    instructions: Path
    state: Path
    cache: Path
    evidence: Path
    drafts: Path


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    chat: ChatConfig = field(default_factory=ChatConfig)
    paths: Paths | None = None


DEFAULT_PATHS = {
    "vault": "vault",
    "raw": "vault/raw",
    "wiki": "vault/wiki",
    "index_md": "vault/index.md",
    "instructions": "instructions",
    "state": "state",
    "cache": ".wiki_cache",
    "evidence": "evidence",
    "drafts": "drafts",
}


def _apply(dc, values: dict, section: str):
    for key, value in values.items():
        if not hasattr(dc, key):
            raise ValueError(f"Unknown setting [{section}] {key} in wiki.toml")
        setattr(dc, key, value)


def load_config(config_path: Path | None = None, root: Path | None = None) -> Config:
    """Read wiki.toml (if present) on top of the defaults above."""
    root = Path(root) if root else PROJECT_ROOT
    config_path = Path(config_path) if config_path else root / "wiki.toml"
    raw: dict = {}
    if config_path.exists():
        with open(config_path, "rb") as f:
            raw = tomllib.load(f)
        root = config_path.resolve().parent

    cfg = Config()
    _apply(cfg.model, raw.get("model", {}), "model")
    _apply(cfg.retrieval, raw.get("retrieval", {}), "retrieval")
    _apply(cfg.chat, raw.get("chat", {}), "chat")

    path_values = {**DEFAULT_PATHS, **raw.get("paths", {})}
    cfg.paths = Paths(root=root, **{k: (root / v).resolve() for k, v in path_values.items()})
    return cfg
