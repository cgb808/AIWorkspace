"""Global pytest configuration: set minimal environment so app imports succeed."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("APP_TEST_MODE", "1")
os.environ.setdefault("SKIP_DB", "1")
os.environ.setdefault("ALLOW_EMBED_FALLBACK", "true")
