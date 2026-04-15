#!/usr/bin/env python3
"""
detect_evaluate_modification.py — detect changes to the evaluate/ folder.

The evaluate/ folder contains scoring, checks, and rules that must not be
modified by contestants. Any file changed, added, or deleted relative to
origin/main is flagged.

Usage:
  python detect_evaluate_modification.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def _ignored_paths() -> list[str]:
    """Comma-separated list of path prefixes (relative to repo root) to ignore."""
    raw = os.environ.get("EVALUATE_IGNORE_PATHS", "")
    return [p.strip() for p in raw.split(",") if p.strip()]


def scan() -> list[str]:
    """Return violation strings for any changes to evaluate/ since origin/main."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main", "--", "evaluate/"],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
    except FileNotFoundError:
        return ["git not found — cannot check evaluate/ modifications"]

    if result.returncode != 0:
        # origin/main may not exist (e.g. shallow clone)
        return []

    ignored = _ignored_paths()
    changed = [
        line.strip() for line in result.stdout.splitlines()
        if line.strip() and not any(line.strip().startswith(p) for p in ignored)
    ]
    if not changed:
        return []

    return [
        f"MODIFIED: {f} — the evaluate/ folder must not be changed"
        for f in changed
    ]


if __name__ == "__main__":
    violations = scan()
    if violations:
        print("ALERT: evaluate/ folder has been modified!\n")
        for v in violations:
            print(f"  {v}")
        print(f"\n{len(violations)} finding(s).")
        sys.exit(1)
    else:
        print("OK: evaluate/ folder is unchanged from origin/main.")
        sys.exit(0)
