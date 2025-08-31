#!/usr/bin/env python3
"""DEPRECATED wrapper.

Use: python scripts/append_log_io.py read ...

Retained temporarily for migration.
"""
from __future__ import annotations
import sys, warnings, runpy

warnings.warn(
    "append_log_reader.py is deprecated; use append_log_io.py read", DeprecationWarning, stacklevel=2
)

argv = [sys.argv[0], 'read'] + sys.argv[1:]
sys.argv = argv
runpy.run_module('scripts.append_log_io', run_name='__main__')
