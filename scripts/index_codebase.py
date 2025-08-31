#!/usr/bin/env python
"""Index the codebase: gather module metadata and populate model registry if missing entries.
Writes to project-index-runtime.json and updates model registry via health.register_model.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
OUT = ROOT / "project-index-runtime.json"

# Lightweight dynamic import for registry population
sys.path.insert(0, str(ROOT))
try:
    from app.health.health_router import get_model_registry, register_model
except Exception as e:  # noqa: BLE001
    print(f"Could not import health router: {e}", file=sys.stderr)
    register_model = None  # type: ignore
    get_model_registry = lambda: []  # type: ignore

EXCLUDE_DIRS = {"__pycache__", "node_modules", ".venv", ".git", "archive"}
PY_SUFFIX = ".py"

extra_excludes = set()
env_excludes = os.getenv("INDEX_EXCLUDE")
if env_excludes:
    for token in env_excludes.split(","):
        token = token.strip()
        if token:
            extra_excludes.add(token)


def should_skip(p: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in p.parts):
        return True
    rel_parts = p.relative_to(ROOT).parts
    # simple prefix match for env provided excludes
    for pat in extra_excludes:
        if pat and rel_parts and rel_parts[0] == pat:
            return True
    return False


modules = []
for path in APP.rglob("*.py"):
    if should_skip(path):
        continue
    rel = path.relative_to(ROOT).as_posix()
    try:
        text = path.read_bytes()
        h = hashlib.sha256(text).hexdigest()[:12]
        loc = text.count(b"\n") + 1
    except Exception as e:  # noqa: BLE001
        h, loc = f"ERR:{e}", 0
    modules.append({"module": rel, "hash": h, "loc": loc})

prev = {}
prev_modules_map = {}
if OUT.exists():
    try:
        prev = json.loads(OUT.read_text())
        for m in prev.get("modules", []):
            prev_modules_map[m["module"]] = m
    except Exception:
        prev = {}

added = []
removed = []
changed = []
current_map = {m["module"]: m for m in modules}
if prev_modules_map:
    prev_keys = set(prev_modules_map)
    curr_keys = set(current_map)
    added = sorted(curr_keys - prev_keys)
    removed = sorted(prev_keys - curr_keys)
    for k in curr_keys & prev_keys:
        if current_map[k]["hash"] != prev_modules_map[k]["hash"]:
            changed.append(k)

summary = {
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "python_version": sys.version.split()[0],
    "module_count": len(modules),
    "modules": modules,
    "diff": {
        "added": added,
        "removed": removed,
        "changed": changed,
        "previous_module_count": len(prev_modules_map) or None,
    },
    "excludes": sorted(list(EXCLUDE_DIRS | extra_excludes)),
}

# Optional: seed additional model metadata from env HINT_MODELS = name:family pairs
hint = os.getenv("HINT_MODELS")
if register_model and hint:
    for token in hint.split(","):
        token = token.strip()
        if not token or ":" not in token:
            continue
        name, family = token.split(":", 1)
        try:
            register_model(name=name, family=family, loaded=False)
        except Exception:
            pass
    summary["models_after_seed"] = get_model_registry()
else:
    try:
        summary["models"] = get_model_registry()
    except Exception:
        pass

OUT.write_text(json.dumps(summary, indent=2))
print(f"Wrote index to {OUT}")
