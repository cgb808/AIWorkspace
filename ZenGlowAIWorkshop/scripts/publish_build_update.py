"""Redis Pub/Sub publisher for build/content updates using msgpack.

Usage (CLI):
  python scripts/publish_build_update.py --content "New model deployed" --artifact models/model.bin
"""
from __future__ import annotations

import argparse
import os
import redis  # type: ignore
import msgpack  # type: ignore
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
CHANNEL = os.getenv("REDIS_BUILD_CHANNEL", "build_updates")

log = logging.getLogger("publish_build_update")
if not log.handlers:
    logging.basicConfig(level=logging.INFO)


def get_redis_client():
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, socket_timeout=5)
    except Exception as e:  # noqa: BLE001
        log.error(f"Redis connection error: {e}")
        raise


def publish_build_update(content: str, extra: Optional[Dict[str, Any]] = None) -> bool:
    message: Dict[str, Any] = {
        "type": "build_update",
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        message.update(extra)
    packed = msgpack.packb(message)
    r = get_redis_client()
    try:
        r.publish(CHANNEL, packed)
        log.info(f"Published build update to {CHANNEL}: {message}")
        return True
    except Exception as e:  # noqa: BLE001
        log.error(f"Publish error: {e}")
        return False


def _parse_args():
    p = argparse.ArgumentParser(description="Publish build/update notification over Redis Pub/Sub")
    p.add_argument("--content", required=True, help="Main update content message")
    p.add_argument("--artifact", help="Optional artifact path")
    p.add_argument("--meta", nargs="*", help="Extra key=value pairs")
    return p.parse_args()


def main():  # pragma: no cover - CLI utility
    args = _parse_args()
    extra: Dict[str, Any] = {}
    if args.artifact:
        extra["artifact_path"] = args.artifact
    if args.meta:
        for kv in args.meta:
            if "=" in kv:
                k, v = kv.split("=", 1)
                extra[k] = v
    ok = publish_build_update(args.content, extra or None)
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
