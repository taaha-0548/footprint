"""Stable identifiers and hashing (Rule 5, Section 5 conventions)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

_PR_KEY = re.compile(r"^(?P<repo>[^/#\s]+/[^/#\s]+)#(?P<num>\d+)$")


def pr_key(owner_repo: str, number: int) -> str:
    return f"{owner_repo}#{number}"


def parse_pr_key(key: str) -> tuple[str, int]:
    m = _PR_KEY.match(key)
    if not m:
        raise ValueError(f"bad pr_key: {key!r}")
    return m["repo"], int(m["num"])


def sha256_obj(obj: Any) -> str:
    """Hash of canonical JSON (sorted keys), independent of dict ordering."""
    data = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
