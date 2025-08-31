"""Package training artifacts into a versioned tar.gz archive.

Includes by default:
  - fine_tuning/training/configs/
  - fine_tuning/datasets/*.md,*.json,*.jsonl (small descriptors)
  - scripts/ensure_phi3_model.sh (ensures model availability)
  - README.md (root)
  - AGENT / ARCHITECTURE docs summary subset (docs/ARCHITECTURE_OVERVIEW.md if present)

Excludes large model weights, checkpoints, .git, caches.

Usage:
  python scripts/package_training_artifacts.py --version 0.1.0
"""
from __future__ import annotations
import os, tarfile, argparse, hashlib, time
from pathlib import Path

INCLUDE_GLOBS = [
    'fine_tuning/training/configs',
    'fine_tuning/datasets',
    'scripts/ensure_phi3_model.sh',
    'README.md',
    'docs/ARCHITECTURE_OVERVIEW.md'
]
TEXT_EXT = {'.md', '.json', '.jsonl', '.yaml', '.yml', '.py', '.sh'}
EXCLUDE_PATTERNS = ['.git', 'checkpoint', 'cache', 'dist', 'build', '__pycache__', '.venv', 'models', 'data/standard']

def should_include(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_PATTERNS:
            return False
    if path.is_dir():
        return True
    if path.suffix.lower() in TEXT_EXT:
        return True
    # small files < 200KB allowed regardless of ext
    try:
        return path.stat().st_size < 200_000
    except Exception:
        return False

def add_path(t: tarfile.TarFile, root: Path, path: Path):
    arcname = path.as_posix()
    t.add(path.as_posix(), arcname=arcname, recursive=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', required=True)
    ap.add_argument('--output-dir', default='artifact')
    args = ap.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime('%Y%m%d')
    fname = f"training_artifacts_v{args.version}_{stamp}.tar.gz"
    fpath = out_dir / fname
    with tarfile.open(fpath, 'w:gz') as tar:
        for pat in INCLUDE_GLOBS:
            p = Path(pat)
            if not p.exists():
                continue
            if p.is_dir():
                for sub in p.rglob('*'):
                    if should_include(sub) and sub.is_file():
                        add_path(tar, p, sub)
            else:
                if should_include(p):
                    add_path(tar, p.parent, p)
    # compute hash
    h = hashlib.sha256()
    with open(fpath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    digest = h.hexdigest()[:16]
    final = out_dir / f"{fpath.stem}_{digest}.tar.gz"
    fpath.rename(final)
    print(f"Created archive: {final}")

if __name__ == '__main__':
    main()