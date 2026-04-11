#!/usr/bin/env python3
"""
detect_templating.py — detect multiline code templates in tt/ that suggest
pre-generated code is being inserted into translations.

The tt tool should translate TypeScript to Python dynamically, not ship
pre-written Python code templates. This check finds multiline string literals
(triple-quoted strings) longer than 2 lines that appear to contain Python code.

Usage:
  python detect_templating.py
  pytest detect_templating.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
TT_ROOT = PROJECT_ROOT / "tt" / "tt"

# Python keywords that suggest a string contains code
CODE_INDICATORS = {
    "def ", "class ", "for ", "while ", "if ", "elif ", "else:",
    "return ", "import ", "from ", "try:", "except", "with ",
    "async def", "await ", "yield ", "lambda ", "raise "
}


def _looks_like_code(text: str) -> bool:
    """Return True if text appears to contain Python code."""
    lines = text.splitlines()
    if len(lines) <= 2:
        return False

    # Check if any line contains code indicators
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(kw) or f" {kw}" in line for kw in CODE_INDICATORS):
            return True
    return False


def scan() -> list[str]:
    """Find multiline string templates containing code in tt/."""
    if not TT_ROOT.exists():
        return []

    # Scan all Python files under tt/tt/
    tt_files = sorted(p for p in TT_ROOT.rglob("*.py") if p.is_file())

    violations: list[str] = []

    for path in tt_files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue

        # Walk AST looking for string constants
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value
                if _looks_like_code(text):
                    # Find the line number
                    lineno = node.lineno if hasattr(node, 'lineno') else 1
                    line_count = len(text.splitlines())
                    violations.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{lineno}: "
                        f"{line_count}-line string template contains pre-generated code"
                    )

    return violations


def test_no_templating():
    """tt must not use pre-generated code templates."""
    violations = scan()
    if violations:
        report = "\n".join(violations)
        raise AssertionError(
            f"Possible pre-generated code templates found ({len(violations)} finding(s)):\n{report}"
        )


if __name__ == "__main__":
    violations = scan()
    if violations:
        print("ALERT: Possible pre-generated code templates found!\n")
        for v in violations:
            print(f"  {v}")
        print(f"\n{len(violations)} finding(s) total.")
        sys.exit(1)
    else:
        print("OK: No pre-generated code templates found.")
        sys.exit(0)
