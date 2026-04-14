#!/usr/bin/env python3
"""Show improvement stats from results.csv.

Usage:
    python scripts/stats.py              # full summary
    python scripts/stats.py --last 10    # last 10 experiments
    python scripts/stats.py --keeps      # only kept experiments
    python scripts/stats.py --csv        # raw CSV to stdout
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_FILE = ROOT / "results.csv"


def load_rows() -> list[dict]:
    if not RESULTS_FILE.exists():
        return []
    with open(RESULTS_FILE, newline="") as f:
        return list(csv.DictReader(f))


def print_table(rows: list[dict], columns: list[str]) -> None:
    """Print rows as a simple aligned table."""
    widths = {c: max(len(c), max((len(str(r.get(c, ""))) for r in rows), default=0)) for c in columns}
    header = "  ".join(c.ljust(widths[c]) for c in columns)
    sep = "  ".join("-" * widths[c] for c in columns)
    print(f"  {header}")
    print(f"  {sep}")
    for r in rows:
        line = "  ".join(str(r.get(c, "")).ljust(widths[c]) for c in columns)
        print(f"  {line}")


def cmd_summary(rows: list[dict]) -> None:
    total = len(rows)
    keeps = sum(1 for r in rows if r["status"] in ("keep", "baseline"))
    discards = sum(1 for r in rows if r["status"] == "discard")
    crashes = sum(1 for r in rows if r["status"] == "crash")
    pending = sum(1 for r in rows if r["status"] == "pending")

    first = rows[0]
    latest = rows[-1]
    best_pass = max(int(r["pass"]) for r in rows)
    first_pass = int(first["pass"])
    total_gain = best_pass - first_pass

    durations = [int(r["duration_s"]) for r in rows if int(r["duration_s"]) > 0]
    avg_dur = sum(durations) // len(durations) if durations else 0

    hit_rate = f"{keeps / total * 100:.0f}" if total > 0 else "0"
    score_est = f"{best_pass / 135 * 85:.1f}"

    print("=" * 64)
    print("  AUTORESEARCH LOOP STATS")
    print("=" * 64)
    print()
    print(f"  Experiments:    {total} total")
    print(f"    Kept:         {keeps}")
    print(f"    Discarded:    {discards}")
    print(f"    Crashed:      {crashes}")
    print(f"    Pending:      {pending}")
    print(f"  Hit rate:       {hit_rate}%")
    print()
    print(f"  First run:      {first['pass']} passed / {first['fail']} failed ({first['timestamp']})")
    print(f"  Latest run:     {latest['pass']} passed / {latest['fail']} failed ({latest['timestamp']})")
    print(f"  Best ever:      {best_pass} passed")
    print(f"  Total gain:     +{total_gain} tests from baseline")
    print()
    print(f"  Avg cycle time: {avg_dur}s")
    print()
    print(f"  Score estimate: {score_est}% (test component, 85% weight)")
    print("=" * 64)

    kept_rows = [r for r in rows if r["status"] in ("keep", "baseline")]
    if kept_rows:
        print()
        print("  IMPROVEMENT TIMELINE:")
        for r in kept_rows:
            p = int(r["pass"])
            bar = "#" * (p // 3)
            print(f"    {r['commit']}  {p:3d}/135  {bar}  {r['description']}")
    print()


def cmd_last(rows: list[dict], n: int) -> None:
    print(f"=== Last {n} experiments ===\n")
    cols = ["timestamp", "commit", "pass", "fail", "new_passes", "new_failures", "duration_s", "status", "description"]
    print_table(rows[-n:], cols)


def cmd_keeps(rows: list[dict]) -> None:
    kept = [r for r in rows if r["status"] in ("keep", "baseline")]
    print("=== Kept experiments (improvements only) ===\n")
    cols = ["timestamp", "commit", "pass", "fail", "duration_s", "description"]
    print_table(kept, cols)


def cmd_csv() -> None:
    if RESULTS_FILE.exists():
        print(RESULTS_FILE.read_text(), end="")


def main() -> None:
    rows = load_rows()
    if not rows:
        print("No results yet. Run: python scripts/evaluate.py 'baseline'")
        return

    args = sys.argv[1:]
    if not args or args[0] == "--summary":
        cmd_summary(rows)
    elif args[0] == "--last":
        n = int(args[1]) if len(args) > 1 else 10
        cmd_last(rows, n)
    elif args[0] == "--keeps":
        cmd_keeps(rows)
    elif args[0] == "--csv":
        cmd_csv()
    else:
        cmd_summary(rows)


if __name__ == "__main__":
    main()
