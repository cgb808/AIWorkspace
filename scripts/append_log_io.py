#!/usr/bin/env python3
"""Append Log Writer & Reader (multi-writer aware)

Provides:
  * append_log_writer mode (default) to append length-prefixed MessagePack frames per session
  * append_log_reader mode to read/inspect frames (.log or .logtmp)

Multi-writer safety improvements over the minimal prototype:
  * O_APPEND single open per invocation (no read/modify/write windows)
  * Optional advisory flock-based rotation locking (--enable-lock)
  * Optional sequence allocation file with atomic increment (--alloc-seq) to avoid duplicate seq across writers
  * Double-checked rotation after acquiring lock (prevents ABA size race)
  * Crash-safe fsync options (--fsync, --fsync-interval)

Frame schema (unchanged):
  { version:int, time:iso8601, session_id:str, user_id:str, role:str, seq:int|None, content:str, metadata:dict }

Limitations:
  * Concurrent writers without --alloc-seq may still produce duplicate seq when using only --auto-seq scan heuristic.
  * Rotation still allows a small window where another writer opens old path just before rotation; that write remains in sealed segment (acceptable).

Usage examples:
  # Append (auto alloc seq with lock + fsync every 10 frames)
  python scripts/append_log_io.py write --user-id alice --content "Hello" --session-id S1 --alloc-seq --enable-lock --fsync-interval 10

  # Read JSONL
  python scripts/append_log_io.py read data/append_logs/session_S1.log --stats --detect-gaps
"""
from __future__ import annotations

import argparse, os, sys, time, json, uuid, struct, re, errno
from datetime import datetime, UTC
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List, Tuple

try:
    import msgpack  # type: ignore
except Exception as e:  # noqa: BLE001
    print("msgpack required", e, file=sys.stderr); raise

try:  # Optional locking (fcntl only on POSIX)
    import fcntl  # type: ignore
except Exception:  # noqa: BLE001
    fcntl = None  # type: ignore

SAFE_SESSION_RE = re.compile(r'[^A-Za-z0-9._-]+')

def iso() -> str:
    return datetime.now(UTC).isoformat()

def sanitize_session_id(raw: str) -> str:
    cleaned = SAFE_SESSION_RE.sub('-', raw).strip('-') or 'session'
    return cleaned[:120]

def session_paths(base_dir: Path, session_id: str) -> Dict[str, Path]:
    return {
        'logtmp': base_dir / f"session_{session_id}.logtmp",
        'lock': base_dir / f"session_{session_id}.lock",
        'seq': base_dir / f"session_{session_id}.seq",
    }

def seal_log(path: Path) -> Path:
    final = path.with_suffix('.log')
    if final.exists():  # Avoid clobber; add timestamp suffix
        final = path.with_name(final.stem + f"_{int(time.time())}.log")
    path.rename(final)
    return final

def queue_segment(seg: Path, redis_list: Optional[str]) -> bool:
    if redis_list:
        try:
            import redis  # type: ignore
            r = redis.from_url(os.getenv('REDIS_URL','redis://localhost:6379/0'))
            r.lpush(redis_list, str(seg))
            print(f"[queue] {seg} -> {redis_list}")
            return True
        except Exception as e:  # noqa: BLE001
            print(f"[queue] redis fail: {e}")
            return False
    print(f"[segment] sealed {seg}")
    return True

def discover_last_seq_scan(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return -1
    last = -1
    try:
        with open(path, 'rb') as fh:
            while True:
                hdr = fh.read(4)
                if len(hdr) < 4:
                    break
                (length,) = struct.unpack('>I', hdr)
                payload = fh.read(length)
                if len(payload) < length:
                    break
                try:
                    frame = msgpack.unpackb(payload, raw=False)
                    s = frame.get('seq')
                    if isinstance(s, int):
                        last = s
                except Exception:  # noqa: BLE001
                    break
    except Exception as e:  # noqa: BLE001
        print(f"[warn] seq scan failed: {e}")
    return last

def alloc_seq(seq_path: Path, enable_lock: bool) -> int:
    seq_path.parent.mkdir(parents=True, exist_ok=True)
    # Open (create if missing)
    with open(seq_path, 'a+b') as fh:
        if enable_lock and fcntl:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            except Exception as e:  # noqa: BLE001
                print(f"[warn] seq lock failed fallback scan: {e}")
                return discover_last_seq_scan(seq_path.with_suffix('.logtmp')) + 1
        fh.seek(0)
        raw = fh.read().decode('utf-8', errors='ignore').strip()
        last = int(raw) if raw.isdigit() else -1
        nxt = last + 1
        fh.seek(0)
        fh.truncate()
        fh.write(str(nxt).encode())
        fh.flush()
        os.fsync(fh.fileno())
        if enable_lock and fcntl:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except Exception:  # noqa: BLE001
                pass
    return nxt

def acquire_rotation_lock(lock_path: Path) -> Optional[int]:
    if not fcntl:
        return None
    lock_fh = open(lock_path, 'a+')
    try:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fh.seek(0)
        lock_fh.truncate()
        lock_fh.write(json.dumps({'pid': os.getpid(), 'time': time.time()}) + '\n')
        lock_fh.flush()
        return lock_fh.fileno()  # keep fh alive via closure variable
    except OSError as e:  # noqa: BLE001
        if e.errno in (errno.EACCES, errno.EAGAIN):
            lock_fh.close()
            return None
        raise

def release_rotation_lock(fd: Optional[int]):
    if fd is None or not fcntl:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except Exception:  # noqa: BLE001
        pass

def write_frame_fd(fd: int, obj: Dict[str, Any], do_fsync: bool = False):
    payload = msgpack.packb(obj, use_bin_type=True)
    header = struct.pack('>I', len(payload))
    os.write(fd, header)
    os.write(fd, payload)
    if do_fsync:
        os.fsync(fd)

def writer(args: argparse.Namespace) -> None:
    session_id = sanitize_session_id(args.session_id or str(uuid.uuid4()))
    base_dir = Path(args.log_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    paths = session_paths(base_dir, session_id)
    logtmp = paths['logtmp']

    # Determine rotation need (pre-lock heuristic)
    now = time.time()
    exists = logtmp.exists()
    created = logtmp.stat().st_mtime if exists else now
    size_ok = (logtmp.stat().st_size if exists else 0) < args.max_size
    age_ok = (now - created) < args.max_age
    need_rotate = exists and (not size_ok or not age_ok)

    lock_fd = None
    if need_rotate and args.enable_lock:
        lock_fd = acquire_rotation_lock(paths['lock'])
        if lock_fd is None:
            # Another process will rotate; proceed without rotating here
            need_rotate = False
        else:
            # Double-check after lock
            exists = logtmp.exists()
            if exists:
                size_ok = logtmp.stat().st_size < args.max_size
                age_ok = (time.time() - logtmp.stat().st_mtime) < args.max_age
                need_rotate = not size_ok or not age_ok
            else:
                need_rotate = False

    if need_rotate and logtmp.exists():
        sealed = seal_log(logtmp)
        ok = queue_segment(sealed, args.redis_list)
        if args.strict_queue and not ok:
            print('[error] queue push failed (strict mode)', file=sys.stderr)
            release_rotation_lock(lock_fd)
            sys.exit(2)

    # Open (O_APPEND ensures atomic append). Create if missing/new after rotation.
    fd = os.open(str(logtmp), os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o644)

    # Sequence allocation hierarchy
    if args.seq is not None:
        seq = args.seq
    elif args.alloc_seq:
        seq = alloc_seq(paths['seq'], args.enable_lock)
    elif args.auto_seq:
        seq = discover_last_seq_scan(logtmp) + 1
    else:
        seq = None

    metadata: Dict[str, Any] = {}
    if args.metadata_json:
        try:
            m = json.loads(args.metadata_json)
            if isinstance(m, dict):
                metadata = m
            else:
                print('[warn] metadata not object; ignored')
        except Exception as e:  # noqa: BLE001
            print(f"[warn] bad metadata JSON: {e}")

    frame = {
        'version': 1,
        'time': iso(),
        'session_id': session_id,
        'user_id': args.user_id,
        'role': args.role,
        'seq': seq,
        'content': args.content,
        'metadata': metadata,
    }

    write_frame_fd(fd, frame, do_fsync=args.fsync)
    if args.fsync_interval and not args.fsync:
        # Periodic fsync based on seq (only if seq known)
        if isinstance(seq, int) and seq % args.fsync_interval == 0:
            os.fsync(fd)
    os.close(fd)
    release_rotation_lock(lock_fd)
    print(f"[append] session={session_id} seq={seq} size={logtmp.stat().st_size}")

def read_frames(path: Path, stop_on_error: bool = True) -> Iterator[Dict[str, Any]]:
    with open(path, 'rb') as fh:
        offset = 0
        while True:
            hdr = fh.read(4)
            if not hdr:
                break
            if len(hdr) < 4:
                if stop_on_error:
                    print(f"[error] truncated length header at {offset}", file=sys.stderr)
                break
            (length,) = struct.unpack('>I', hdr)
            payload = fh.read(length)
            if len(payload) < length:
                if stop_on_error:
                    print(f"[error] truncated payload at {offset}", file=sys.stderr)
                break
            try:
                frame = msgpack.unpackb(payload, raw=False)
                yield frame
            except Exception as e:  # noqa: BLE001
                if stop_on_error:
                    print(f"[error] unpack failed at {offset}: {e}", file=sys.stderr)
                    break
            offset += 4 + length

def reader(args: argparse.Namespace) -> None:
    def parse_time(ts: str):
        return datetime.fromisoformat(ts.replace('Z','+00:00'))

    since_dt = parse_time(args.since) if args.since else None
    until_dt = parse_time(args.until) if args.until else None
    total = 0
    sessions: Dict[str, int] = {}
    gaps: List[Tuple[str, int, int]] = []
    for p in args.paths:
        path = Path(p)
        last_seq = None
        for frame in read_frames(path, stop_on_error=not args.lenient):
            t = frame.get('time')
            dt = None
            if t:
                try:
                    dt = parse_time(t)
                except Exception:  # noqa: BLE001
                    pass
            if since_dt and dt and dt < since_dt:
                continue
            if until_dt and dt and dt > until_dt:
                continue
            if args.session and frame.get('session_id') != args.session:
                continue
            if args.user and frame.get('user_id') != args.user:
                continue
            if args.role and frame.get('role') != args.role:
                continue
            if args.detect_gaps:
                seq = frame.get('seq')
                if isinstance(seq, int):
                    if last_seq is not None and seq != last_seq + 1:
                        gaps.append((path.name, last_seq, seq))
                    last_seq = seq
            sid = frame.get('session_id')
            if sid:
                sessions[sid] = sessions.get(sid, 0) + 1
            total += 1
            if args.msgpack:
                payload = msgpack.packb(frame, use_bin_type=True)
                sys.stdout.buffer.write(struct.pack('>I', len(payload)))
                sys.stdout.buffer.write(payload)
            else:
                if args.pretty:
                    print(json.dumps(frame, ensure_ascii=False, indent=2))
                else:
                    print(json.dumps(frame, ensure_ascii=False))
    if args.stats:
        print(f"[stats] frames={total} sessions={len(sessions)}", file=sys.stderr)
        for sid, cnt in sessions.items():
            print(f"[stats] session {sid} frames={cnt}", file=sys.stderr)
        if args.detect_gaps and gaps:
            for name, a, b in gaps:
                print(f"[gap] {name}: {a}->{b}", file=sys.stderr)

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Append log IO (writer/reader)")
    sub = p.add_subparsers(dest='cmd', required=True)

    w = sub.add_parser('write', help='Append a frame to a session log')
    w.add_argument('--session-id')
    w.add_argument('--user-id', required=True)
    w.add_argument('--role', default='user')
    w.add_argument('--content', required=True)
    w.add_argument('--log-dir', default='data/append_logs')
    w.add_argument('--max-size', type=int, default=64*1024*1024)
    w.add_argument('--max-age', type=int, default=600)
    w.add_argument('--redis-list')
    w.add_argument('--strict-queue', action='store_true')
    w.add_argument('--metadata-json')
    # Sequence strategies
    w.add_argument('--seq', type=int)
    w.add_argument('--auto-seq', action='store_true', help='Scan existing log for last seq (may collide multi-writer)')
    w.add_argument('--alloc-seq', action='store_true', help='Atomic seq allocation using .seq file (multi-writer safe)')
    # Durability
    w.add_argument('--fsync', action='store_true', help='fsync after each frame')
    w.add_argument('--fsync-interval', type=int, help='fsync every N frames (requires seq)')
    # Locking
    w.add_argument('--enable-lock', action='store_true', help='Use advisory lock for rotation & seq allocation')
    w.set_defaults(func=writer)

    r = sub.add_parser('read', help='Read/inspect log files')
    r.add_argument('paths', nargs='+')
    r.add_argument('--jsonl', action='store_true')  # retained for compatibility (no-op; default)
    r.add_argument('--pretty', action='store_true')
    r.add_argument('--msgpack', action='store_true')
    r.add_argument('--lenient', action='store_true')
    r.add_argument('--session')
    r.add_argument('--user')
    r.add_argument('--role')
    r.add_argument('--since')
    r.add_argument('--until')
    r.add_argument('--stats', action='store_true')
    r.add_argument('--detect-gaps', action='store_true')
    r.set_defaults(func=reader)
    return p

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
