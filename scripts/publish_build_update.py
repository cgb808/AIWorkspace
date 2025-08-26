"""
Redis Pub/Sub publisher for build/content updates using msgpack.
Run this script to notify other Copilot agents about new build content.
"""
def publish_build_update(content: str, extra: dict = None):
import os
import redis
import msgpack
import logging
from datetime import datetime, timezone

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
CHANNEL = os.getenv("REDIS_BUILD_CHANNEL", "build_updates")

logging.basicConfig(level=logging.INFO)

def get_redis_client():
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, socket_timeout=5)
    except Exception as e:
        logging.error(f"Redis connection error: {e}")
        raise

def publish_build_update(content: str, extra: dict = None):
    message = {
        "type": "build_update",
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if extra:
        message.update(extra)
    packed = msgpack.packb(message)
    r = get_redis_client()
    try:
        r.publish(CHANNEL, packed)
        logging.info(f"Published build update to {CHANNEL}: {message}")
    except Exception as e:
        logging.error(f"Publish error: {e}")

# Example usage
if __name__ == "__main__":
    publish_build_update("New build artifact available", {"artifact_path": "/path/to/artifact"})
