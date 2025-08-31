"""Push a schema JSON file to a running Weaviate instance.

Usage:
  python scripts/push_weaviate_schema.py --file hybrid_schema.json [--endpoint http://127.0.0.1:8080]

Environment:
  WEAVIATE_ENDPOINT (default http://127.0.0.1:8080)

The file should contain a full schema payload acceptable to POST /v1/schema (or it will attempt class-by-class creation).
If POST /v1/schema fails with 422 and object is a dict containing 'classes', it will attempt per-class creation.
"""
from __future__ import annotations
import os, json, argparse, sys, time
import requests

def post(url: str, payload: dict):
    r = requests.post(url, json=payload, timeout=30)
    return r

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', required=True)
    ap.add_argument('--endpoint', help='Weaviate base URL')
    args = ap.parse_args()
    endpoint = args.endpoint or os.getenv('WEAVIATE_ENDPOINT', 'http://127.0.0.1:8080')
    with open(args.file, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    base = endpoint.rstrip('/') + '/v1/schema'
    # Detect single-class object
    if isinstance(schema, dict) and 'class' in schema and 'properties' in schema:
        r = post(base + '/classes', schema)
        if r.status_code in (200, 201):
            print(f"[weaviate] Created class {schema.get('class')}")
            return
        print(f"[weaviate] Failed single class: {r.status_code} {r.text}")
        sys.exit(1)
    # Full schema attempt
    r = post(base, schema)
    if r.status_code in (200, 204):
        print('[weaviate] Schema applied (full).')
        return
    if r.status_code == 422 and isinstance(schema, dict) and 'classes' in schema:
        print('[weaviate] Full schema POST failed; attempting per-class.')
        ok = True
        for cls in schema['classes']:
            cr = post(base + '/classes', cls)
            if cr.status_code not in (200, 201):
                print(f"[weaviate] Failed class {cls.get('class')}: {cr.status_code} {cr.text}")
                ok = False
            else:
                print(f"[weaviate] Created class {cls.get('class')}")
            time.sleep(0.25)
        if not ok:
            sys.exit(1)
        return
    print(f"[weaviate] Failed applying schema: {r.status_code} {r.text}")
    sys.exit(1)

if __name__ == '__main__':
    main()