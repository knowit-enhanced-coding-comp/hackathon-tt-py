#!/usr/bin/env python3
"""Update the status of the last experiment in results.csv.

Usage:
    python scripts/mark.py keep
    python scripts/mark.py discard
    python scripts/mark.py baseline
    python scripts/mark.py crash
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_FILE = ROOT / "results.csv"
VALID = {"keep", "discard", "baseline", "crash", "pending"}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in VALID:
        print(f"Usage: python scripts/mark.py <{'|'.join(sorted(VALID))}>")
        sys.exit(1)

    status = sys.argv[1]

    if not RESULTS_FILE.exists():
        print("No results file found.")
        sys.exit(1)

    with open(RESULTS_FILE, newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("No experiments to mark.")
        sys.exit(1)

    rows[-1]["status"] = status

    fieldnames = list(rows[0].keys())
    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Marked last experiment as: {status}")


if __name__ == "__main__":
    main()
