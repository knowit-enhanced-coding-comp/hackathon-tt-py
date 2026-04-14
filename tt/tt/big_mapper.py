"""
Big.js → Python Decimal expression translator.

Translates Big.js expression strings (as TypeScript source text) into
Python Decimal-equivalent expression strings. Operates on source text,
not AST nodes.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

_BIG_PATTERN = re.compile(r"\bnew\s+Big\s*\(|(?<!\w)Big\s*\(")


def is_big_expression(ts_expr: str) -> bool:
    """Return True if the expression contains Big.js patterns.

    Args:
        ts_expr: A TypeScript expression string.

    Returns:
        True if the string contains ``new Big(...)`` or ``Big(...)`` patterns.
    """
    return bool(_BIG_PATTERN.search(ts_expr))


# ---------------------------------------------------------------------------
# Constructor translation
# ---------------------------------------------------------------------------

def _translate_constructors(expr: str) -> str:
    """Replace ``new Big(v)`` and ``Big(v)`` with ``Decimal(str(v))``."""
    # new Big(value) → Decimal(str(value))
    expr = re.sub(
        r"\bnew\s+Big\s*\(([^)]*)\)",
        lambda m: f"Decimal(str({m.group(1).strip()}))",
        expr,
    )
    # Big(0) identity → Decimal('0')  (literal zero)
    expr = re.sub(
        r"(?<!\w)Big\s*\(\s*0\s*\)",
        "Decimal('0')",
        expr,
    )
    # Big(value) → Decimal(str(value))
    expr = re.sub(
        r"(?<!\w)Big\s*\(([^)]*)\)",
        lambda m: f"Decimal(str({m.group(1).strip()}))",
        expr,
    )
    return expr


# ---------------------------------------------------------------------------
# Method-chain translation helpers
# ---------------------------------------------------------------------------

# Arithmetic chains: .plus(x) → + x, etc.
_ARITHMETIC_METHODS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\.plus\s*\(([^)]*)\)"), "+ {arg}"),
    (re.compile(r"\.minus\s*\(([^)]*)\)"), "- {arg}"),
    (re.compile(r"\.mul\s*\(([^)]*)\)"), "* {arg}"),
    (re.compile(r"\.div\s*\(([^)]*)\)"), "/ {arg}"),
    (re.compile(r"\.add\s*\(([^)]*)\)"), "+ {arg}"),  # alias used in TS source
]

# Comparison chains: .eq(x) → == x, etc.
_COMPARISON_METHODS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\.eq\s*\(([^)]*)\)"), "== {arg}"),
    (re.compile(r"\.gt\s*\(([^)]*)\)"), "> {arg}"),
    (re.compile(r"\.lt\s*\(([^)]*)\)"), "< {arg}"),
    (re.compile(r"\.gte\s*\(([^)]*)\)"), ">= {arg}"),
    (re.compile(r"\.lte\s*\(([^)]*)\)"), "<= {arg}"),
]


def _translate_method_chains(expr: str) -> str:
    """Translate Big.js method chains to Python infix operators."""
    for pattern, template in _ARITHMETIC_METHODS + _COMPARISON_METHODS:
        expr = pattern.sub(
            lambda m, t=template: " " + t.format(arg=m.group(1).strip()),
            expr,
        )
    return expr


# ---------------------------------------------------------------------------
# Conversion method translation
# ---------------------------------------------------------------------------

def _translate_conversions(expr: str) -> str:
    """Translate ``.toNumber()`` and ``.toFixed(n)`` conversions."""
    # .toFixed(n) — must come before .toNumber() to avoid partial match
    # Wraps the preceding expression: expr.toFixed(n) → round(expr, n)
    # We handle this as a suffix replacement; the caller expression is left as-is
    # and we emit round(..., n) by wrapping the whole thing at a higher level.
    # For text-level translation we replace the suffix pattern.
    expr = re.sub(
        r"\.toFixed\s*\(([^)]*)\)",
        lambda m: f", {m.group(1).strip()})",  # appended to round( prefix added below
        expr,
    )
    # .toNumber() → float(...)
    expr = re.sub(r"\.toNumber\s*\(\s*\)", "", expr)
    return expr


def _wrap_to_fixed(expr: str) -> str:
    """Wrap expressions that end with ``, n)`` (from toFixed) in ``round(...)``."""
    # After _translate_conversions, a toFixed call leaves ", n)" at the end.
    # We need to wrap the base expression in round().
    # Pattern: <base>, <n>) at end of string
    match = re.search(r"^(.*),\s*(\d+)\)$", expr, re.DOTALL)
    if match:
        base = match.group(1).strip()
        n = match.group(2).strip()
        return f"round({base}, {n})"
    return expr


def _wrap_to_number(original: str, translated: str) -> str:
    """If original had .toNumber(), wrap translated expression in float()."""
    if re.search(r"\.toNumber\s*\(\s*\)", original):
        return f"float({translated})"
    return translated


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def translate_big_expression(ts_expr: str) -> str:
    """Translate a Big.js expression string to Python Decimal equivalent.

    Handles constructors (``new Big(v)``, ``Big(v)``), arithmetic method
    chains (``.plus``, ``.minus``, ``.mul``, ``.div``), comparison chains
    (``.eq``, ``.gt``, ``.lt``, ``.gte``, ``.lte``), and conversions
    (``.toNumber()``, ``.toFixed(n)``).

    Args:
        ts_expr: A TypeScript expression string containing Big.js calls.

    Returns:
        A Python expression string using ``Decimal`` arithmetic.
    """
    had_to_number = bool(re.search(r"\.toNumber\s*\(\s*\)", ts_expr))
    had_to_fixed = bool(re.search(r"\.toFixed\s*\(", ts_expr))

    result = ts_expr

    # 1. Translate constructors
    result = _translate_constructors(result)

    # 2. Translate method chains (arithmetic + comparison)
    result = _translate_method_chains(result)

    # 3. Handle conversions
    if had_to_fixed:
        # Remove .toFixed(n) suffix and remember n
        m = re.search(r"\.toFixed\s*\(([^)]*)\)", result)
        if m:
            n = m.group(1).strip()
            base = result[: m.start()].strip()
            result = f"round({base}, {n})"
    elif had_to_number:
        # Remove .toNumber() and wrap in float()
        result = re.sub(r"\.toNumber\s*\(\s*\)", "", result).strip()
        result = f"float({result})"

    logger.debug("translate_big_expression: %r → %r", ts_expr, result)
    return result
