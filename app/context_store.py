"""Simple shared context storage for the main agent.

Keeps a succinct .context/context.txt file with subagent interactions.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


ROOT_DIR = Path(__file__).resolve().parent.parent
CONTEXT_DIR = ROOT_DIR / ".context"
CONTEXT_FILE = CONTEXT_DIR / "context.txt"


def ensure_context_dir() -> None:
    CONTEXT_DIR.mkdir(exist_ok=True)


def read_context() -> str:
    ensure_context_dir()
    if not CONTEXT_FILE.exists():
        return ""
    return CONTEXT_FILE.read_text(encoding="utf-8")


def append_context(line: str, max_lines: int = 40) -> str:
    """Appends a line and keeps the file short (last max_lines)."""

    ensure_context_dir()
    clean_line = " ".join(line.strip().split())
    existing: List[str] = []
    if CONTEXT_FILE.exists():
        existing = [l.rstrip("\n") for l in CONTEXT_FILE.read_text(encoding="utf-8").splitlines()]

    updated = (existing + [clean_line])[-max_lines:]
    CONTEXT_FILE.write_text("\n".join(updated) + "\n", encoding="utf-8")
    return "\n".join(updated)


def clear_context() -> None:
    """Zera o arquivo de contexto no início de uma execução do agente principal."""

    ensure_context_dir()
    CONTEXT_FILE.write_text("", encoding="utf-8")


__all__ = [
    "append_context",
    "clear_context",
    "CONTEXT_DIR",
    "CONTEXT_FILE",
    "ensure_context_dir",
    "read_context",
]
