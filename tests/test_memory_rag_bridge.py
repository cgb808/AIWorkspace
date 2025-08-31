"""Tests for `fine_tuning.tooling.rag.memory_rag_bridge`.

Focus:
 - Offset sidecar resume logic (`_load_stored_offset`, `_persist_offset_if_needed`).
 - Dedup + ingestion flow (embed + DB insert mocked).
 - Search path (`--search`) uses embed_texts and prints scores.

We avoid real DB/network by monkeypatching psycopg2.connect and requests.post.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import types
from pathlib import Path

import pytest


class _FakeCursor:
    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):  # minimal pattern matching
        self.store.setdefault("exec", []).append((sql, params))
        if "SELECT content_hash" in sql:
            # return current dedup rows (empty first time)
            self._results = [(h,) for h in self.store.get("dedup", set())]
        elif sql.strip().startswith("SELECT chunk"):
            # similarity search: return 1 fake row
            self._results = [("example memory text", 0.9)]
        else:
            self._results = []

    def fetchall(self):
        return getattr(self, "_results", [])

    def close(self):  # pragma: no cover
        pass


class _FakeConn:
    def __init__(self, store):
        self.store = store

    def cursor(self):
        return _FakeCursor(self.store)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def close(self):  # pragma: no cover
        pass


def _fake_requests_post(embed_calls_store):
    class _Resp:
        def __init__(self, vecs):
            self.vecs = vecs
            self.status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"embeddings": self.vecs}

    def _post(url, json, timeout):  # noqa: D401
        texts = json["texts"]
        embed_calls_store.append(list(texts))
        # produce 2-dim vectors for determinism
        return _Resp([[1.0, 0.0] for _ in texts])

    return _post


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    # Provide required env vars; MEMORY_FILE_PATH points at temp file we control.
    mem_file = tmp_path / "memory.jsonl"
    monkeypatch.setenv("MEMORY_FILE_PATH", str(mem_file))
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h:5432/db")
    yield


def _write_memory_lines(mem_path: Path, lines):
    with mem_path.open("w", encoding="utf-8") as f:
        for obj in lines:
            f.write(json.dumps(obj) + "\n")


def _install_fake_psycopg2(store):
    """Install a fake psycopg2 package (with extras) into sys.modules for import.

    We emulate the minimal surface used by memory_rag_bridge: connect, OperationalError,
    InterfaceError, and execute_values in psycopg2.extras.
    """
    pkg = types.ModuleType("psycopg2")
    pkg.__path__ = []  # make it package-like

    class _Err(Exception):
        pass

    pkg.OperationalError = _Err
    pkg.InterfaceError = _Err
    pkg.connect = lambda dsn: _FakeConn(store)

    extras = types.ModuleType("psycopg2.extras")

    def execute_values(cur, sql, rows, template=None, page_size=None, fetch=False, fetchall=None, **kwargs):  # noqa: D401
        # Record inserts for potential assertions (mimic signature superset)
        cur.store.setdefault("execute_values", []).append((sql, rows))
        if fetch:
            # Simulate RETURNING id, chunk by enumerating
            return [(i + 1, r[1] if len(r) > 1 else None) for i, r in enumerate(rows)]

    extras.execute_values = execute_values
    sys.modules["psycopg2"] = pkg
    sys.modules["psycopg2.extras"] = extras


def test_offset_persistence_resume(monkeypatch, tmp_path):
    mem_path = Path(os.environ["MEMORY_FILE_PATH"])
    # First run: two lines ingested
    _write_memory_lines(mem_path, [
        {"id": 1, "content": "alpha first"},
        {"id": 2, "content": "beta second"},
    ])
    store = {"dedup": set()}
    _install_fake_psycopg2(store)
    import requests as _requests  # real module; we'll patch post
    embed_calls = []
    monkeypatch.setattr(_requests, "post", _fake_requests_post(embed_calls))
    # Ensure argparse doesn't parse pytest args
    monkeypatch.setattr(sys, "argv", ["memory_rag_bridge", "--once"])  # we will override once flag anyway
    bridge = importlib.import_module("fine_tuning.tooling.rag.memory_rag_bridge")
    bridge = importlib.reload(bridge)
    # Speed up: avoid actual sleeps in backoff
    monkeypatch.setattr(bridge.time, "sleep", lambda s: None)
    # Force ARGS.once True for single pass
    bridge.ARGS.once = True
    bridge.process_new()
    # Sidecar should exist
    sidecar = Path(str(mem_path) + ".offset.json")
    assert sidecar.exists()
    first_offset = json.loads(sidecar.read_text())["offset"]
    assert first_offset > 0
    # Depending on BATCH_SIZE both lines may be embedded in one batch
    all_embedded = [t for batch in embed_calls for t in batch]
    assert set(all_embedded) == {"alpha first", "beta second"}

    # Append a third line and rerun; should resume (not re-embed first two)
    _write_memory_lines(mem_path, [
        {"id": 1, "content": "alpha first"},
        {"id": 2, "content": "beta second"},
        {"id": 3, "content": "gamma third"},
    ])
    embed_calls.clear()
    monkeypatch.setattr(sys, "argv", ["memory_rag_bridge", "--once"])  # reset for reload
    bridge = importlib.reload(bridge)
    monkeypatch.setattr(bridge.time, "sleep", lambda s: None)
    bridge.ARGS.once = True
    bridge.process_new()
    all_embedded2 = [t for batch in embed_calls for t in batch]
    assert all_embedded2 == ["gamma third"]


def test_retry_backoff_final_failure(monkeypatch, tmp_path):
    # Simulate embedding endpoint failing all retries to ensure SystemExit raised.
    mem_path = Path(os.environ["MEMORY_FILE_PATH"])
    _write_memory_lines(mem_path, [{"id": 1, "content": "only line"}])
    store = {"dedup": set()}
    _install_fake_psycopg2(store)

    class _RespFail:
        status_code = 500
        def raise_for_status(self):
            raise RuntimeError("server 500")

    def _bad_post(*a, **k):
        return _RespFail()

    import requests as _req
    monkeypatch.setattr(_req, "post", _bad_post)
    monkeypatch.setattr(sys, "argv", ["memory_rag_bridge", "--once"])  # limit to once
    bridge = importlib.import_module("fine_tuning.tooling.rag.memory_rag_bridge")
    bridge = importlib.reload(bridge)
    monkeypatch.setattr(bridge.time, "sleep", lambda s: None)
    bridge.EMBED_RETRIES = 2  # speed
    bridge.ARGS.once = True
    with pytest.raises(SystemExit):
        bridge.process_new()


def test_search_path(monkeypatch, tmp_path, capsys):
    # Provide a stub embed that returns fixed vector and stub DB returning one row.
    store = {"dedup": set()}
    _install_fake_psycopg2(store)
    import requests as _req
    monkeypatch.setattr(_req, "post", _fake_requests_post([]))
    monkeypatch.setattr(sys, "argv", ["memory_rag_bridge"])  # no extra args
    bridge = importlib.import_module("fine_tuning.tooling.rag.memory_rag_bridge")
    bridge = importlib.reload(bridge)
    monkeypatch.setattr(bridge.time, "sleep", lambda s: None)
    # Emulate CLI: --search "query"
    bridge.ARGS.search = "test query"
    bridge.ARGS.top_k = 3
    bridge.main()
    out = capsys.readouterr().out
    assert "example memory text" in out
