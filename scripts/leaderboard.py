#!/usr/bin/env python3
"""Leaderboard analytics from the Supabase competition database.

Usage:
    python scripts/leaderboard.py                  # full analysis
    python scripts/leaderboard.py --leaderboard     # ranked leaderboard only
    python scripts/leaderboard.py --team NAME       # deep dive on one team
    python scripts/leaderboard.py --history         # all submissions over time
    python scripts/leaderboard.py --checks          # rule compliance breakdown
    python scripts/leaderboard.py --quality         # code quality comparison
    python scripts/leaderboard.py --us              # our team's position and gaps
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Load .env
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip("\"'")
        if k and k not in os.environ:
            os.environ[k] = v

from supabase import create_client, Client  # noqa: E402


def get_client() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
        sys.exit(1)
    return create_client(url, key)


def fetch_leaderboard(sb: Client, project: str = "ghostfolio", legal_only: bool = False) -> list[dict]:
    query = sb.table("submissions").select("*").eq("project", project).order("overall", desc=True)
    if legal_only:
        query = query.eq("legal", True)
    resp = query.execute()
    # Deduplicate: best per team
    best: dict[str, dict] = {}
    for row in resp.data:
        team = row["team"]
        if team not in best or (row["overall"] or 0) > (best[team]["overall"] or 0):
            best[team] = row
    return sorted(best.values(), key=lambda r: r.get("overall") or 0, reverse=True)


def fetch_all_submissions(sb: Client, project: str = "ghostfolio") -> list[dict]:
    resp = sb.table("submissions").select("*").eq("project", project).order("submitted_at", desc=False).execute()
    return resp.data


def fetch_team_submissions(sb: Client, team: str, project: str = "ghostfolio") -> list[dict]:
    resp = sb.table("submissions").select("*").eq("project", project).eq("team", team).order("submitted_at", desc=False).execute()
    return resp.data


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_leaderboard(rows: list[dict]) -> None:
    print()
    print("=" * 90)
    print("  LEADERBOARD (ghostfolio)")
    print("=" * 90)
    print(f"  {'#':>3}  {'Team':<30} {'Overall':>8} {'Tests%':>8} {'Quality%':>9} {'Grade':>6} {'Legal':>6}")
    print(f"  {'---':>3}  {'-'*30:<30} {'--------':>8} {'------':>8} {'---------':>9} {'-----':>6} {'-----':>6}")
    for i, row in enumerate(rows, 1):
        team = row.get("team", "?")[:30]
        overall = row.get("overall") or 0
        tests = row.get("tests_pct") or 0
        quality = row.get("quality_pct") or 0
        grade = row.get("quality_weighted_grade") or "?"
        legal = "Yes" if row.get("legal") else "NO"
        print(f"  {i:>3}  {team:<30} {overall:>8.1f} {tests:>8.1f} {quality:>9.1f} {grade:>6} {legal:>6}")
    print("=" * 90)
    print(f"  {len(rows)} teams")
    print()


def print_quality_comparison(rows: list[dict]) -> None:
    print()
    print("=" * 110)
    print("  CODE QUALITY BREAKDOWN")
    print("=" * 110)
    print(f"  {'Team':<25} {'Health':>7} {'Complex':>8} {'DeadCode':>9} {'Dupl':>6} {'Coupling':>9} {'Deps':>6} {'Arch':>6} {'Grade':>6}")
    print(f"  {'-'*25:<25} {'-------':>7} {'--------':>8} {'---------':>9} {'------':>6} {'---------':>9} {'------':>6} {'------':>6} {'------':>6}")
    for row in rows:
        team = row.get("team", "?")[:25]
        health = row.get("quality_translated_health") or 0
        compl = row.get("translated_complexity_score") or 0
        dead = row.get("translated_dead_code_score") or 0
        dupl = row.get("translated_duplication_score") or 0
        coup = row.get("translated_coupling_score") or 0
        deps = row.get("translated_dependency_score") or 0
        arch = row.get("translated_architecture_score") or 0
        grade = row.get("quality_weighted_grade") or "?"
        print(f"  {team:<25} {health:>7.0f} {compl:>8.0f} {dead:>9.0f} {dupl:>6.0f} {coup:>9.0f} {deps:>6.0f} {arch:>6.0f} {grade:>6}")
    print("=" * 110)
    print()


def print_checks_breakdown(rows: list[dict]) -> None:
    print()
    print("=" * 90)
    print("  RULE COMPLIANCE")
    print("=" * 90)

    # Collect all check names
    all_checks: set[str] = set()
    for row in rows:
        checks = row.get("checks") or {}
        all_checks.update(checks.keys())
    check_names = sorted(all_checks)

    if not check_names:
        print("  No check data available.")
        print()
        return

    # Header
    header = f"  {'Team':<25}"
    for cn in check_names:
        short = cn[:15]
        header += f" {short:>15}"
    header += f"  {'Valid':>6}"
    print(header)
    print(f"  {'-'*25}" + "".join(f" {'-'*15}" for _ in check_names) + f"  {'------':>6}")

    for row in rows:
        team = row.get("team", "?")[:25]
        checks = row.get("checks") or {}
        valid = "Yes" if row.get("valid_checks") else "NO"
        line = f"  {team:<25}"
        for cn in check_names:
            status = checks.get(cn, "-")
            line += f" {status:>15}"
        line += f"  {valid:>6}"
        print(line)
    print("=" * 90)
    print()


def print_history(rows: list[dict]) -> None:
    print()
    print("=" * 100)
    print("  ALL SUBMISSIONS (chronological)")
    print("=" * 100)
    print(f"  {'Time':<22} {'Team':<25} {'Overall':>8} {'Tests%':>8} {'Quality%':>9} {'Legal':>6}")
    print(f"  {'-'*22:<22} {'-'*25:<25} {'--------':>8} {'------':>8} {'---------':>9} {'-----':>6}")
    for row in rows:
        ts = (row.get("submitted_at") or "?")[:22]
        team = (row.get("team") or "?")[:25]
        overall = row.get("overall") or 0
        tests = row.get("tests_pct") or 0
        quality = row.get("quality_pct") or 0
        legal = "Yes" if row.get("legal") else "NO"
        print(f"  {ts:<22} {team:<25} {overall:>8.1f} {tests:>8.1f} {quality:>9.1f} {legal:>6}")
    print("=" * 100)
    print(f"  {len(rows)} submissions total")
    print()


def print_team_deep_dive(rows: list[dict], team: str) -> None:
    print()
    print("=" * 90)
    print(f"  TEAM DEEP DIVE: {team}")
    print("=" * 90)
    if not rows:
        print("  No submissions found.")
        print()
        return

    print(f"\n  Submissions: {len(rows)}")
    best = max(rows, key=lambda r: r.get("overall") or 0)
    latest = rows[-1]

    print(f"  Best score:   {best.get('overall', 0):.1f} (tests: {best.get('tests_pct', 0):.1f}%, quality: {best.get('quality_pct', 0):.1f}%)")
    print(f"  Latest score: {latest.get('overall', 0):.1f} (tests: {latest.get('tests_pct', 0):.1f}%, quality: {latest.get('quality_pct', 0):.1f}%)")

    print(f"\n  Progression:")
    for row in rows:
        ts = (row.get("submitted_at") or "?")[:19]
        overall = row.get("overall") or 0
        tests = row.get("tests_pct") or 0
        legal = "legal" if row.get("legal") else "ILLEGAL"
        bar = "#" * int(overall / 2)
        print(f"    {ts}  {overall:>6.1f}  {bar}  (tests: {tests:.0f}%, {legal})")

    checks = latest.get("checks") or {}
    if checks:
        print(f"\n  Latest checks:")
        for k, v in checks.items():
            status_icon = "OK" if v == "OK" else ("SKIP" if v == "SKIPPED" else "FAIL")
            print(f"    [{status_icon:>4}] {k}")
    print()


def print_our_position(leaderboard: list[dict], our_team: str) -> None:
    print()
    print("=" * 90)
    print(f"  OUR POSITION: {our_team}")
    print("=" * 90)

    our_row = None
    our_rank = 0
    for i, row in enumerate(leaderboard, 1):
        if row.get("team", "").lower() == our_team.lower():
            our_row = row
            our_rank = i
            break

    if not our_row:
        print(f"  Team '{our_team}' not found in leaderboard. Have you published results?")
        print()
        return

    print(f"\n  Rank: #{our_rank} of {len(leaderboard)}")
    print(f"  Overall: {our_row.get('overall', 0):.1f}")
    print(f"  Tests:   {our_row.get('tests_pct', 0):.1f}%")
    print(f"  Quality: {our_row.get('quality_pct', 0):.1f}%")
    print(f"  Grade:   {our_row.get('quality_weighted_grade', '?')}")

    # Gap analysis
    if our_rank > 1:
        above = leaderboard[our_rank - 2]
        gap = (above.get("overall") or 0) - (our_row.get("overall") or 0)
        print(f"\n  Gap to #{our_rank - 1} ({above.get('team', '?')}): {gap:.1f} points")
        test_gap = (above.get("tests_pct") or 0) - (our_row.get("tests_pct") or 0)
        qual_gap = (above.get("quality_pct") or 0) - (our_row.get("quality_pct") or 0)
        print(f"    Tests gap:   {test_gap:+.1f}%")
        print(f"    Quality gap: {qual_gap:+.1f}%")

    if our_rank < len(leaderboard):
        below = leaderboard[our_rank]
        lead = (our_row.get("overall") or 0) - (below.get("overall") or 0)
        print(f"\n  Lead over #{our_rank + 1} ({below.get('team', '?')}): +{lead:.1f} points")

    # Where to improve
    tests_pct = our_row.get("tests_pct") or 0
    quality_pct = our_row.get("quality_pct") or 0
    print(f"\n  Improvement leverage:")
    print(f"    +10% tests   = +{10 * 0.5:.1f} overall points")
    print(f"    +10% quality = +{10 * 0.5:.1f} overall points")
    if tests_pct < 100:
        print(f"    Tests headroom:   {100 - tests_pct:.1f}% remaining")
    else:
        print(f"    Tests: MAXED at 100%")
    print(f"    Quality headroom: {100 - quality_pct:.1f}% remaining")
    print()


def main() -> None:
    sb = get_client()
    our_team = os.environ.get("TEAM_NAME", "Gutta Consulting")
    args = sys.argv[1:]

    if not args or args[0] == "--all":
        # Full analysis
        leaderboard = fetch_leaderboard(sb)
        print_leaderboard(leaderboard)
        print_our_position(leaderboard, our_team)
        print_quality_comparison(leaderboard)
        print_checks_breakdown(leaderboard)
    elif args[0] == "--leaderboard":
        print_leaderboard(fetch_leaderboard(sb))
    elif args[0] == "--team":
        team = args[1] if len(args) > 1 else our_team
        rows = fetch_team_submissions(sb, team)
        print_team_deep_dive(rows, team)
    elif args[0] == "--history":
        print_history(fetch_all_submissions(sb))
    elif args[0] == "--checks":
        print_checks_breakdown(fetch_leaderboard(sb))
    elif args[0] == "--quality":
        print_quality_comparison(fetch_leaderboard(sb))
    elif args[0] == "--us":
        leaderboard = fetch_leaderboard(sb)
        print_our_position(leaderboard, our_team)
        rows = fetch_team_submissions(sb, our_team)
        print_team_deep_dive(rows, our_team)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
