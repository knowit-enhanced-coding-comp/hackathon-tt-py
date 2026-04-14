#!/usr/bin/env python3
"""Run translate+test cycle and record metrics to results.csv.

Usage:
    python scripts/evaluate.py "description of what changed"
"""
from __future__ import annotations

import csv
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_FILE = ROOT / "results.csv"
RUNS_DIR = ROOT / "runs"
FIELDS = [
    "timestamp", "commit", "pass", "fail", "error",
    "new_passes", "new_failures", "duration_s", "status", "description",
]

LAST_PASSED = RUNS_DIR / ".last_passed_tests"
LAST_FAILED = RUNS_DIR / ".last_failed_tests"


def init_csv() -> None:
    if not RESULTS_FILE.exists() or RESULTS_FILE.stat().st_size == 0:
        with open(RESULTS_FILE, "w", newline="") as f:
            csv.writer(f).writerow(FIELDS)


def read_previous_best() -> int:
    if not RESULTS_FILE.exists():
        return 0
    with open(RESULTS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        return max((int(row["pass"]) for row in reader), default=0)


def get_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=7", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def kill_server() -> None:
    subprocess.run(
        ["bash", str(ROOT / "projecttests/tools/kill_ghostfolio_pytx.sh")],
        capture_output=True,
    )


def run_translate() -> float:
    print("=== TRANSLATE ===")
    t0 = time.monotonic()
    result = subprocess.run(
        ["uv", "run", "--project", str(ROOT / "tt"), "tt", "translate"],
        cwd=ROOT, capture_output=True, text=True,
    )
    elapsed = time.monotonic() - t0
    # Show last few lines of output
    for line in result.stdout.strip().splitlines()[-5:]:
        print(f"  {line}")
    if result.returncode != 0:
        print(f"  TRANSLATE FAILED (exit {result.returncode})")
        for line in result.stderr.strip().splitlines()[-5:]:
            print(f"  {line}")
    print(f"  Translate took {elapsed:.1f}s")
    return elapsed


def run_tests() -> tuple[float, str]:
    """Start server, run pytest, return (elapsed_seconds, raw_output)."""
    print("\n=== TEST ===")
    pytx_dir = ROOT / "translations" / "ghostfolio_pytx"
    port = "3335"

    # Sync deps for both the translated project and the tt project (has pytest)
    subprocess.run(
        ["uv", "sync", "--project", str(pytx_dir), "--extra", "dev", "--quiet"],
        capture_output=True,
    )
    subprocess.run(
        ["uv", "sync", "--project", str(ROOT / "tt"), "--extra", "dev", "--quiet"],
        capture_output=True,
    )

    # Start server
    server = subprocess.Popen(
        ["uv", "run", "python", "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", port, "--log-level", "warning"],
        cwd=pytx_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    try:
        # Wait for health
        import urllib.request
        for i in range(30):
            try:
                urllib.request.urlopen(f"http://localhost:{port}/api/v1/health", timeout=1)
                break
            except Exception:
                if i == 29:
                    print("  ERROR: Server did not start")
                    return 0.0, ""
                time.sleep(1)

        # Run pytest
        t0 = time.monotonic()
        env = {**__import__("os").environ, "GHOSTFOLIO_API_URL": f"http://localhost:{port}"}
        result = subprocess.run(
            ["uv", "run", "--project", str(ROOT / "tt"), "pytest",
             str(ROOT / "projecttests" / "ghostfolio_api"), "-v"],
            cwd=ROOT, capture_output=True, text=True, env=env,
        )
        elapsed = time.monotonic() - t0
        output = result.stdout + result.stderr
        return elapsed, output
    finally:
        server.terminate()
        server.wait(timeout=5)
        kill_server()


def parse_results(output: str) -> tuple[int, int, int, list[str], list[str]]:
    """Parse pytest -v output. Returns (passed, failed, errors, pass_names, fail_names)."""
    passed_names: list[str] = []
    failed_names: list[str] = []
    error_count = 0

    for line in output.splitlines():
        line = line.strip()
        if " PASSED" in line and line.startswith("projecttests/"):
            name = line.split(" ")[0]
            passed_names.append(name)
        elif " FAILED" in line and line.startswith("projecttests/"):
            name = line.split(" ")[0]
            failed_names.append(name)
        elif " ERROR" in line and line.startswith("projecttests/"):
            error_count += 1

    return len(passed_names), len(failed_names), error_count, sorted(passed_names), sorted(failed_names)


def compute_diffs(
    current_passed: list[str], current_failed: list[str]
) -> tuple[list[str], list[str]]:
    """Compare against previous run. Returns (new_passes, new_failures)."""
    prev_passed: set[str] = set()
    prev_failed: set[str] = set()

    if LAST_PASSED.exists():
        prev_passed = set(LAST_PASSED.read_text().strip().splitlines())
    if LAST_FAILED.exists():
        prev_failed = set(LAST_FAILED.read_text().strip().splitlines())

    new_passes = sorted(set(current_passed) - prev_passed)
    new_failures = sorted(prev_passed - set(current_passed))  # were passing, now aren't

    # Save current state for next run
    LAST_PASSED.write_text("\n".join(current_passed) + "\n" if current_passed else "")
    LAST_FAILED.write_text("\n".join(current_failed) + "\n" if current_failed else "")

    return new_passes, new_failures


def main() -> None:
    description = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "no description"
    RUNS_DIR.mkdir(exist_ok=True)
    init_csv()

    prev_best = read_previous_best()
    commit = get_commit()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    kill_server()

    translate_time = run_translate()
    test_time, raw_output = run_tests()
    duration = int(translate_time + test_time)

    # Save raw log
    log_file = RUNS_DIR / f"run_{timestamp.replace(':', '-')}.log"
    log_file.write_text(raw_output)

    if not raw_output:
        # Server crash
        row = {
            "timestamp": timestamp, "commit": commit,
            "pass": 0, "fail": 0, "error": 0,
            "new_passes": 0, "new_failures": 0,
            "duration_s": duration, "status": "crash",
            "description": description,
        }
        with open(RESULTS_FILE, "a", newline="") as f:
            csv.DictWriter(f, FIELDS).writerow(row)
        print(f"\n  CRASH. Log: {log_file}")
        sys.exit(1)

    pass_count, fail_count, error_count, passed_names, failed_names = parse_results(raw_output)
    new_passes, new_failures = compute_diffs(passed_names, failed_names)

    delta = pass_count - prev_best
    if pass_count > prev_best and len(new_failures) == 0:
        suggestion = "KEEP"
    elif pass_count == prev_best and len(new_failures) == 0:
        suggestion = "NEUTRAL"
    else:
        suggestion = "DISCARD"

    # Print summary
    print()
    print("=" * 64)
    print(f"  RESULTS: {pass_count} passed / {fail_count} failed / {error_count} errors")
    print(f"  DELTA:   {delta:+d} from previous best ({prev_best})")
    print(f"  TIME:    {duration}s (translate: {translate_time:.0f}s, test: {test_time:.0f}s)")
    print(f"  STATUS:  {suggestion}")
    print("=" * 64)

    if new_passes:
        print(f"\n  NEW PASSES ({len(new_passes)}):")
        for t in new_passes:
            print(f"    + {t}")

    if new_failures:
        print(f"\n  REGRESSIONS ({len(new_failures)}):")
        for t in new_failures:
            print(f"    - {t}")

    print(f"\n  Log: {log_file}")
    print("=" * 64)

    # Append to CSV
    row = {
        "timestamp": timestamp, "commit": commit,
        "pass": pass_count, "fail": fail_count, "error": error_count,
        "new_passes": len(new_passes), "new_failures": len(new_failures),
        "duration_s": duration, "status": "pending",
        "description": description,
    }
    with open(RESULTS_FILE, "a", newline="") as f:
        csv.DictWriter(f, FIELDS).writerow(row)


if __name__ == "__main__":
    main()
