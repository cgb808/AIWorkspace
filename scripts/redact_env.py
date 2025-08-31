#!/usr/bin/env python
"""Redact a .env file for safe sharing.

Heuristics:
  - Any variable name containing one of: KEY, SECRET, PASS, TOKEN, PASSWORD, PAT, API_KEY, CLIENT_SECRET is considered sensitive.
  - Special cases:
      * SUPABASE_URL kept intact (non-secret project URL) unless --strict supplied.
      * DATABASE_URL: keep scheme://user:***@host:port/db (mask password & optionally username with --paranoid).
  - For sensitive values output format (default): <REDACTED:len=NN> (optionally prefix first 4 chars with --prefix)
  - Lines that are comments or blank are passed through unchanged.

Usage:
  python scripts/redact_env.py               # reads .env, writes .env.redacted
  python scripts/redact_env.py --input my.env --output safe.env
  cat .env | python scripts/redact_env.py -  # read from stdin

Exit codes: 0 success, 1 error.
"""
from __future__ import annotations

import argparse
import re
import sys
from typing import Iterable

SENSITIVE_MARKERS = [
    "KEY",
    "SECRET",
    "PASS",
    "TOKEN",
    "PASSWORD",
    "PAT",
    "API_KEY",
    "CLIENT_SECRET",
]
ALLOWED_EXCEPTIONS = {"SUPABASE_URL"}
VAR_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(=)(.*)$")


def is_sensitive(name: str, strict: bool) -> bool:
    if not strict and name in ALLOWED_EXCEPTIONS:
        return False
    up = name.upper()
    return any(m in up for m in SENSITIVE_MARKERS)


def redact_value(name: str, value: str, prefix_chars: int, paranoid: bool) -> str:
    if name == "DATABASE_URL":
        # scheme://user:pass@host:port/db?query
        m = re.match(
            r"^(?P<scheme>\w+?)://(?:(?P<user>[^:@/]+)(?::(?P<pw>[^@/]*))?@)?(?P<rest>.*)$",
            value,
        )
        if m:
            user = m.group("user") or ""
            if paranoid and user:
                user = "***"
            return f"{m.group('scheme')}://{user + ('@' if user else '')}***@{m.group('rest')}"
    # Generic sensitive redaction
    if prefix_chars > 0 and len(value) > prefix_chars:
        prefix = value[:prefix_chars]
        return f"{prefix}<REDACTED:len={len(value)}>"
    return f"<REDACTED:len={len(value)}>"


def process_lines(
    lines: Iterable[str], strict: bool, prefix: int, paranoid: bool
) -> Iterable[str]:
    for line in lines:
        raw = line.rstrip("\n")
        if not raw or raw.lstrip().startswith("#"):
            yield raw
            continue
        m = VAR_RE.match(raw)
        if not m:
            yield raw
            continue
        name, eq, val = m.groups()
        # Preserve surrounding quotes for structure detection
        stripped = val.strip()
        if is_sensitive(name, strict):
            redacted_core = redact_value(name, stripped, prefix, paranoid)
            # keep quotes if original had them
            if (
                stripped.startswith(('"', "'"))
                and stripped.endswith(('"', "'"))
                and len(stripped) >= 2
            ):
                quote = stripped[0]
                redacted_core = quote + redacted_core + quote
            yield f"{name}{eq}{redacted_core}"
        else:
            # Optionally truncate very long non-sensitive values
            if len(stripped) > 400:
                yield f"{name}{eq}{stripped[:100]}<...truncated:{len(stripped)}>"
            else:
                yield raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input", "-i", default=".env", help="Input .env file or - for stdin"
    )
    ap.add_argument(
        "--output", "-o", default=".env.redacted", help="Output file (or - for stdout)"
    )
    ap.add_argument("--strict", action="store_true", help="Redact even SUPABASE_URL")
    ap.add_argument(
        "--prefix",
        type=int,
        default=0,
        help="Show first N chars before redaction marker",
    )
    ap.add_argument(
        "--paranoid",
        action="store_true",
        help="Also mask database username in DATABASE_URL",
    )
    args = ap.parse_args()

    try:
        if args.input == "-":
            in_lines = sys.stdin.readlines()
        else:
            with open(args.input, "r", encoding="utf-8") as f:
                in_lines = f.readlines()
    except OSError as e:
        print(f"ERROR: reading input: {e}", file=sys.stderr)
        return 1

    out_lines = list(process_lines(in_lines, args.strict, args.prefix, args.paranoid))

    try:
        if args.output == "-":
            for l in out_lines:
                print(l)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                for l in out_lines:
                    f.write(l + "\n")
    except OSError as e:
        print(f"ERROR: writing output: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
