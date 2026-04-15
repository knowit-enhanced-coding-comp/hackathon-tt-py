#!/usr/bin/env python3
"""
thorough_review.py — Claude-assisted thorough review of the tt translator source.

Reviews every Python file under tt/tt/ for rule breaches, with particular focus
on *prefabricated logic*: domain-specific business implementations that should
have come from translated TypeScript source, not been hand-written into the
translation tool or its scaffold.

This is invoked as part of `make publish_final_results` and determines the
`manual_validation` boolean submitted to the final_submissions table.

Prerequisites:
  ANTHROPIC_API_KEY environment variable must be set.

Usage:
  uv run --project tt python evaluate/scoring/thorough_review.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
TT_SRC_ROOT = REPO_ROOT / "tt" / "tt"

SYSTEM_PROMPT = """\
You are a strict code reviewer for a TypeScript-to-Python translation tool called "tt".

Rules the tool MUST follow:
- Translation is performed by regex-based passes over raw TypeScript source.
- The tool may contain: regex rules, scaffolding templates (FastAPI wiring,
  auth plumbing, route stubs), file IO, CLI code, and generic infrastructure.
- The tool MUST NOT contain prefabricated domain logic. Prefabricated logic is
  any hand-written implementation of project business rules (e.g. portfolio
  performance math, BUY/SELL/DIVIDEND activity handling, financial formulas,
  chart computation, price lookups, aggregation of investments) that should
  instead be produced by translating the TypeScript source.

Review the provided Python file and decide whether it contains rule breaches,
with particular focus on prefabricated domain logic.

A violation is present when the file contains:
- Domain-specific calculations or financial formulas
- Event/activity-type handling encoding domain semantics
- Large string-literal templates that smuggle domain logic
- Any non-trivial function body implementing business rules rather than
  generic translation mechanics or infrastructure

NOT a violation:
- Regex translation passes (even if numerous)
- Generic scaffolding (FastAPI routes, auth, user store, HTTP plumbing)
- CLI argument parsing / file IO
- Stubs that raise NotImplementedError or return {}

Respond with a JSON object (no markdown, no extra text):
{
  "has_violation": true | false,
  "severity": "high" | "medium" | "low" | "none",
  "summary": "one-sentence verdict",
  "findings": [
    {"function": "name", "line": int_or_null, "reason": "why this breaches the rules"}
  ]
}
If has_violation is false, findings must be empty.
"""


def _source_files() -> list[Path]:
    if not TT_SRC_ROOT.exists():
        return []
    return sorted(
        p for p in TT_SRC_ROOT.rglob("*.py")
        if p.is_file() and "__pycache__" not in p.parts
    )


def _review_file(client, path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    relative = path.relative_to(REPO_ROOT)

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"File: {relative}\n\n"
                    "```python\n"
                    f"{source}\n"
                    "```"
                ),
            }
        ],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except Exception as exc:
        return {
            "has_violation": False,
            "severity": "none",
            "summary": f"Could not parse LLM response: {exc}",
            "findings": [],
            "raw_response": raw,
        }


def run_review(verbose: bool = True) -> tuple[bool, list[str]]:
    """
    Run thorough review across tt/tt/*.py.

    Returns (manual_validation, findings).
      manual_validation = True  -> no violations, safe to publish
      manual_validation = False -> violations detected, manually flagged
    """
    try:
        import anthropic
    except ImportError:
        print(
            "ERROR: 'anthropic' package not installed. "
            "Run: uv add --project tt anthropic",
            file=sys.stderr,
        )
        return False, ["anthropic package not installed"]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        return False, ["ANTHROPIC_API_KEY not set"]

    client = anthropic.Anthropic(api_key=api_key)
    findings: list[str] = []

    files = _source_files()
    if verbose:
        print(f"Thorough review: scanning {len(files)} file(s) under {TT_SRC_ROOT.relative_to(REPO_ROOT)} …")

    for path in files:
        relative = path.relative_to(REPO_ROOT)
        if verbose:
            print(f"  Reviewing {relative} …", flush=True)

        result = _review_file(client, path)

        if result.get("has_violation"):
            severity = result.get("severity", "?")
            summary = result.get("summary", "")
            findings.append(f"{relative}: [{severity.upper()}] {summary}")
            for finding in result.get("findings", []):
                fn = finding.get("function", "?")
                line = finding.get("line")
                reason = finding.get("reason", "")
                loc = f":{line}" if line else ""
                findings.append(f"  {relative}{loc}: {fn} — {reason}")

    manual_validation = len(findings) == 0
    return manual_validation, findings


def main() -> int:
    print("=" * 70)
    print("  Thorough Claude review of tt/ source")
    print("=" * 70)
    manual_validation, findings = run_review(verbose=True)
    print()
    if manual_validation:
        print("OK: No rule breaches detected. manual_validation = true")
        return 0
    print("ALERT: Rule breaches detected. manual_validation = false")
    for f in findings:
        print(f"  {f}")
    print(f"\n{len(findings)} finding(s) total.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
