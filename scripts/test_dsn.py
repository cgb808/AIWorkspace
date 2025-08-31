#!/usr/bin/env python
"""Test a Postgres DSN connectivity and print basic info."""
from __future__ import annotations

import os
import re
import socket
import sys

import psycopg2


def main():
    # Args: [--ipv4] <dsn?>
    use_ipv4 = False
    args = [a for a in sys.argv[1:]]
    if args and args[0] == "--ipv4":
        use_ipv4 = True
        args = args[1:]
    if args:
        dsn = args[0]
    else:
        dsn = (
            os.getenv("DATABASE_URL")
            or os.getenv("SUPABASE_DB_URL")
            or os.getenv("SUPABASE_DIRECT_URL")
            or os.getenv("SUPABASE_POOLER_URL")
        )
    if not dsn:
        print("No DSN provided", file=sys.stderr)
        return 2
    if use_ipv4:
        m = re.match(r"^(?P<prefix>.+@)(?P<host>[^/:?]+)(?P<rest>.*)$", dsn)
        if m:
            host = m.group("host")
            try:
                infos = socket.getaddrinfo(
                    host, None, family=socket.AF_INET, type=socket.SOCK_STREAM
                )
                if infos:
                    ipv4 = infos[0][4][0]
                    dsn = f"{m.group('prefix')}{ipv4}{m.group('rest')}"
                    print(f"Rewrote host {host} -> {ipv4}")
            except Exception as e:
                print(f"IPv4 resolution failed: {e}")
    print(f"Connecting to: {dsn[:110]}...")
    try:
        conn = psycopg2.connect(dsn)
    except Exception as e:
        print(f"CONNECT ERROR: {e}")
        return 1
    with conn.cursor() as cur:
        cur.execute("SELECT current_user, version();")
        row = cur.fetchone()
        if row:
            user, version = row
            print(f"current_user={user}")
            print(version.split("\n")[0])
        else:
            print("No row returned from version query")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
