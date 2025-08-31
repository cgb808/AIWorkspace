#!/usr/bin/env python3
"""DEPRECATED wrapper.

Use: python scripts/append_log_io.py write ...

This legacy entry point is retained for backwards compatibility and will be removed.
"""
from __future__ import annotations
import sys, warnings, runpy

warnings.warn(
    "append_log_writer.py is deprecated; use append_log_io.py write", DeprecationWarning, stacklevel=2
)

# Translate legacy args (no subcommand) into new form.
argv = [sys.argv[0], 'write'] + sys.argv[1:]
sys.argv = argv
runpy.run_module('scripts.append_log_io', run_name='__main__')
