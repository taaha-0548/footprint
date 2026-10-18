from pathlib import Path

import pytest

from fps.util.ids import parse_pr_key, pr_key, sha256_obj
from fps.util.jsonl import JsonlWriter, read_jsonl


def test_pr_key_roundtrip() -> None:
    assert parse_pr_key(pr_key("a/b", 7)) == ("a/b", 7)
    with pytest.raises(ValueError):
        parse_pr_key("nope")


def test_hash_ignores_key_order() -> None:
    assert sha256_obj({"a": 1, "b": 2}) == sha256_obj({"b": 2, "a": 1})


def test_jsonl_writer_resumes_and_skips_done(tmp_path: Path) -> None:
    p = tmp_path / "x.jsonl"
    w = JsonlWriter(p)
    assert w.write({"pr_key": "a/b#1", "v": 1})
    assert not w.write({"pr_key": "a/b#1", "v": 2})
    w2 = JsonlWriter(p)  # simulated rerun
    assert not w2.write({"pr_key": "a/b#1", "v": 3})
    assert w2.write({"pr_key": "a/b#2", "v": 4})
    assert [r["v"] for r in read_jsonl(p)] == [1, 4]
