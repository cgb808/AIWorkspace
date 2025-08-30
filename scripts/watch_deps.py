#!/usr/bin/env python
"""Watch critical dependency availability (imports) and log if they disappear.
Uses watchdog to monitor site-packages directory for deletions/renames.
Falls back to periodic import checks if watchdog not installed.
"""
import os, sys, time, importlib, logging

CRITICAL = ["transformers", "torch", "fastapi", "redis"]
INTERVAL = float(os.getenv("DEP_WATCH_INTERVAL", "10"))

logging.basicConfig(level=logging.INFO, format="[depwatch] %(asctime)s %(levelname)s %(message)s")

def check_imports():
    missing = []
    for name in CRITICAL:
        try:
            importlib.import_module(name)
        except Exception:
            missing.append(name)
    if missing:
        logging.error("missing_deps %s", missing)
    else:
        logging.info("all_deps_present")
    return missing

def main():
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except Exception:
        logging.warning("watchdog_not_available_fallback_poll")
        while True:
            check_imports()
            time.sleep(INTERVAL)
    # Use watchdog
    class Handler(FileSystemEventHandler):
        def on_any_event(self, event):  # type: ignore
            miss = check_imports()
            if miss:
                logging.error("deps_missing_after_event %s", miss)
    observer = Observer()
    # Heuristic: site-packages path from one resolved module
    root_file = importlib.import_module('fastapi').__file__ or ''
    root = os.path.dirname(root_file)  # type: ignore[arg-type]
    site_root = os.path.dirname(root)
    observer.schedule(Handler(), site_root, recursive=True)
    observer.start()
    logging.info("dependency_watcher_started path=%s interval=%s", site_root, INTERVAL)
    try:
        while True:
            time.sleep(INTERVAL)
            check_imports()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    check_imports()
    main()
