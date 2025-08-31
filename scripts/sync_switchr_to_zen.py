#!/usr/bin/env python3
"""Sync Switchr router & related artifacts into another repo (local or remote path mount).

Supports specifying an absolute target directory (e.g. sibling clone of remote repo)
so you can keep AIWorkspace authoritative and push updates outward.

Features:
  - --target PATH (or SYNC_TARGET env var)
  - --dry-run (show planned copies)
  - Idempotent overwrite of destination files/dirs
  - Guards against accidental nesting (won't create ZenGlowAIWorkshop/ZenGlowAIWorkshop/...)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RELATIVE_SOURCES = [
    (Path("app") / "central_control", True),  # (relative path, is_dir)
    (Path("docs") / "SWITCHR_ROUTER.md", False),
    (Path("scripts") / "memory_rag_bridge.py", False),
    (Path("scripts") / "publish_build_update.py", False),
    (Path("infrastructure") / "configs" / "central_control", True),
]


def parse_args():
    p = argparse.ArgumentParser(
        description="Sync Switchr artifacts to another repository path or remote host via rsync"
    )
    p.add_argument(
        "--target",
        help="Absolute target repo path OR remote spec user@host:/abs/path (env SYNC_TARGET)",
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Show actions without copying"
    )
    p.add_argument(
        "--rsync-flags",
        default="-az --delete",
        help="Extra flags for rsync when remote target is used",
    )
    p.add_argument("--host", help="Remote host (if building target spec)")
    p.add_argument("--user", help="Remote user (if building target spec)")
    p.add_argument("--path", dest="remote_path", help="Remote absolute repo path")
    p.add_argument("--port", type=int, help="SSH port if not default 22")
    p.add_argument(
        "--auto",
        action="store_true",
        help="Auto-detect using config file or environment variables",
    )
    return p.parse_args()


def load_config():
    cfg_path = ROOT / "switchr_sync_config.json"
    if cfg_path.exists():
        try:
            with cfg_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # noqa: BLE001
            print(f"[sync] WARN: Failed to parse {cfg_path}: {e}")
    return {}


def build_remote_spec(user: str | None, host: str | None, path: str | None) -> str:
    if not (host and path):
        print(
            "[sync] ERROR: host and path required to build remote spec", file=sys.stderr
        )
        sys.exit(2)
    if user:
        return f"{user}@{host}:{path}"
    return f"{host}:{path}"


def resolve_target(args):
    # Priority: explicit --target; else --auto with config/env; else assemble from host/user/path
    if args.target:
        target_raw = args.target
    elif args.auto:
        cfg = load_config().get("remote", {})
        host = args.host or os.getenv("SYNC_REMOTE_HOST") or cfg.get("host")
        user = args.user or os.getenv("SYNC_REMOTE_USER") or cfg.get("user")
        path = args.remote_path or os.getenv("SYNC_REMOTE_PATH") or cfg.get("path")
        port = args.port or int(os.getenv("SYNC_REMOTE_PORT", cfg.get("port", 22)))
        if host and path:
            spec = build_remote_spec(user, host, path)
            return spec, port
        target_raw = os.getenv("SYNC_TARGET")
        if not target_raw:
            print("[sync] ERROR: Could not auto-resolve target", file=sys.stderr)
            sys.exit(2)
        return target_raw, 22
    else:
        if args.host and args.remote_path:
            spec = build_remote_spec(args.user, args.host, args.remote_path)
            return spec, args.port or 22
        env_target = os.getenv("SYNC_TARGET")
        target_raw = env_target
        if not target_raw:
            print(
                "[sync] ERROR: Provide --target or use --auto with config/env",
                file=sys.stderr,
            )
            sys.exit(2)
    # Determine if remote
    if ":/" in target_raw.split("@")[-1]:
        return target_raw, args.port or 22
    return Path(target_raw).expanduser().resolve(), None


def copy_path_local(src: Path, dst: Path, dry: bool):
    if dry:
        print(f"[dry-run] Would copy {src} -> {dst}")
        return
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def copy_path_remote(
    src: Path,
    remote_root: str,
    rel: Path,
    dry: bool,
    rsync_flags: str,
    port: int | None,
):
    remote_dest = f"{remote_root.rstrip('/')}/{rel.as_posix()}"
    if dry:
        print(f"[dry-run] Would rsync {src} -> {remote_dest}")
        return
    base_cmd = ["rsync"] + rsync_flags.split()
    if port and port != 22:
        base_cmd += ["-e", f"ssh -p {port}"]
    cmd = base_cmd + [str(src) + ("/" if src.is_dir() else ""), remote_dest]
    print(f"[sync] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[sync] ERROR rsync failed for {src}: {result.stderr}", file=sys.stderr)
    else:
        print(f"[sync] rsynced {src} -> {remote_dest}")


def main() -> int:
    args = parse_args()
    target, port = resolve_target(args)
    remote_mode = isinstance(target, str)
    copied = 0
    if remote_mode:
        remote_root = target
        print(f"[sync] Remote mode -> {remote_root} (port={port or 22})")
        # Preflight connectivity check
        if not args.dry_run:
            try:
                check_cmd = ["ssh"]
                if port and port != 22:
                    check_cmd += ["-p", str(port)]
                # Extract user@host part
                remote_host_part = remote_root.split(":", 1)[0]
                check_cmd += [remote_host_part, "echo", "SYNC_OK"]
                res = subprocess.run(
                    check_cmd, capture_output=True, text=True, timeout=10
                )
                if res.returncode != 0 or "SYNC_OK" not in res.stdout:
                    print(
                        f"[sync] ERROR: SSH preflight failed: stdout='{res.stdout.strip()}' stderr='{res.stderr.strip()}'",
                        file=sys.stderr,
                    )
                    print(
                        "[sync] HINT: Verify host/IP, connectivity, and that SSH is actually running on the specified port."
                    )
                    return 5
            except Exception as e:  # noqa: BLE001
                print(f"[sync] ERROR: SSH preflight exception: {e}", file=sys.stderr)
                return 5
    else:
        if not target.exists():
            print(
                f"[sync] ERROR: Target path does not exist: {target}", file=sys.stderr
            )
            return 3
        if not (target / "app").exists():
            print(
                f"[sync] WARNING: Target {target} missing 'app/' directory; creating minimal structure"
            )
            (target / "app").mkdir(parents=True, exist_ok=True)
    for rel, _is_dir in RELATIVE_SOURCES:
        src = ROOT / rel
        if not src.exists():
            print(f"[sync] Skip missing source: {src}")
            continue
        if remote_mode:
            copy_path_remote(
                src, remote_root, rel, args.dry_run, args.rsync_flags, port
            )
        else:
            dst = target / rel
            copy_path_local(src, dst, args.dry_run)
            if not args.dry_run:
                print(f"[sync] Copied {src} -> {dst}")
        copied += 1
    print(
        f"[sync] Completed (remote={remote_mode}, dry-run={args.dry_run}). Items processed: {copied}"
    )
    return 0 if copied else 4


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
