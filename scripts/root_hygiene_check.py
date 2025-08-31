#!/usr/bin/env python
"""Root Hygiene Checker

Scans repository root for markdown files outside the allowed allowlist.
Exits with non-zero if violations found (optional future CI integration).

Current Behavior:
  - Print table of violations.
  - Suggest relocation target based on heuristics.

Allowlist matches policy in COPILOT.md.
"""
from __future__ import annotations
import os, sys, re, json

ALLOWED_ROOT = {
    'README.md','COPILOT.md','Makefile','docker-compose.yml','docker-compose-fixed.yml','kong.yml',
    'package.json','package-lock.json','project-index.json','project-index-runtime.json','settings.json',
    'pytest.ini','run_tests.sh','.gitignore',
    # Explicit developer reminder file (allowed):
    'BACKUP_LARGE_FILES.md'
}

def suggest_target(name: str) -> str:
    lower = name.lower()
    if 'policy' in lower or 'rls' in lower:
        return 'docs/security/' + name
    if 'remote' in lower or 'workspace' in lower:
        return 'docs/workspace/' + name
    if 'backup' in lower or 'large' in lower:
        return 'docs/devops/' + name
    if 'rag' in lower or 'integration' in lower:
        return 'docs/' + name
    if 'todo' in lower or 'devops' in lower:
        return ''  # likely delete (empty placeholder)
    return 'docs/' + name

def main():
    root = os.getcwd()
    violations = []
    for entry in os.listdir(root):
        if not entry.endswith('.md'):
            continue
        if entry in ALLOWED_ROOT:
            continue
        # Skip directories masquerading (safety)
        if os.path.isdir(os.path.join(root, entry)):
            continue
        size = os.path.getsize(os.path.join(root, entry))
        target = suggest_target(entry)
        violations.append({
            'file': entry,
            'bytes': size,
            'suggested': target or '(remove)',
            'empty': size == 0
        })
    if not violations:
        print('[root-hygiene] OK - no violations')
        return 0
    print('[root-hygiene] Found', len(violations), 'violations:')
    for v in violations:
        print(f" - {v['file']:30} size={v['bytes']:4} -> {v['suggested']}")
    # Non-zero only if any non-empty (enforcement light mode)
    if any(not v['empty'] for v in violations):
        return 2
    return 0

if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
