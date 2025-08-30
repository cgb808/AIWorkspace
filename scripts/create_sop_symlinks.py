#!/usr/bin/env python3
"""Utility to ensure AI_TERMINAL_SOP.md is present (as symlink) in common workspace roots / venvs.

Idempotent: re-runs won't duplicate. Falls back to copying if symlink creation fails (e.g., on certain filesystems).

Usage:
  python scripts/create_sop_symlinks.py --paths .venv frontend infrastructure || true

Default behavior (no args): will attempt a curated set of likely env roots: .venv, frontend, infrastructure, scripts.
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

CANONICAL = Path('AI_TERMINAL_SOP.md').resolve()

DEFAULT_TARGETS = [
    Path('.venv'),
    Path('frontend'),
    Path('infrastructure'),
    Path('scripts'),
]

def ensure_symlink(target_dir: Path) -> str:
    target_dir = target_dir.resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        return f"SKIP {target_dir} (not a dir)"
    link_path = target_dir / 'AI_TERMINAL_SOP.md'
    if link_path.exists():
        # Validate it references canonical
        try:
            if link_path.is_symlink():
                dest = link_path.resolve()
                if dest == CANONICAL:
                    return f"OK {link_path} (already symlink)"
                else:
                    return f"WARN {link_path} points elsewhere -> {dest}"
            else:
                return f"PRESENT {link_path} (regular file)"
        except OSError as e:
            return f"ERROR stat {link_path}: {e}"
    # Try create symlink
    try:
        rel_target = os.path.relpath(CANONICAL, start=target_dir)
        link_path.symlink_to(rel_target)
        return f"CREATED symlink {link_path} -> {rel_target}"
    except OSError as e:
        # Fallback: copy content
        try:
            data = CANONICAL.read_text(encoding='utf-8')
            link_path.write_text(data, encoding='utf-8')
            return f"COPIED {link_path} (symlink failed: {e})"
        except Exception as e2:
            return f"FAIL {link_path}: {e2}"

def main():
    parser = argparse.ArgumentParser(description='Ensure SOP symlinks exist in target directories.')
    parser.add_argument('--paths', nargs='*', help='Target directories (default preset list)')
    args = parser.parse_args()

    targets = [Path(p) for p in args.paths] if args.paths else DEFAULT_TARGETS

    if not CANONICAL.exists():
        print(f"Canonical SOP not found at {CANONICAL}", file=sys.stderr)
        sys.exit(1)

    results = [ensure_symlink(t) for t in targets]
    for r in results:
        print(r)

if __name__ == '__main__':
    main()
