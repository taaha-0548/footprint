"""Append-only, resumable JSONL keyed by a stable ID (Rule 6)."""
from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def done_keys(path: Path, key: str = "pr_key") -> set[str]:
    return {rec[key] for rec in read_jsonl(path) if key in rec}


class JsonlWriter:
    """Appends records, skipping keys already present in the file."""

    def __init__(self, path: Path, key: str = "pr_key") -> None:
        self.path = path
        self.key = key
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.seen = done_keys(path, key)

    def write(self, rec: dict[str, Any]) -> bool:
        k = rec[self.key]
        if k in self.seen:
            return False
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
        self.seen.add(k)
        return True
