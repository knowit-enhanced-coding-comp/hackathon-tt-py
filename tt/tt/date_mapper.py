"""
date-fns → Python datetime expression translator.

Maps date-fns function call patterns (as TypeScript source text strings)
to Python datetime equivalents. Operates on source text, not AST nodes.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Required imports
# ---------------------------------------------------------------------------

_REQUIRED_IMPORTS: list[str] = [
    "from datetime import datetime, timedelta",
]


def get_required_imports() -> list[str]:
    """Return Python import statements needed for date translations.

    Returns:
        A list of Python import statement strings.
    """
    return list(_REQUIRED_IMPORTS)


# ---------------------------------------------------------------------------
# Translation patterns
# ---------------------------------------------------------------------------

# Each entry: (compiled pattern, replacement template or callable)
# Patterns are tried in order; first match wins.

def _translate_format(m: re.Match[str]) -> str:
    date_arg = m.group(1).strip()
    fmt_arg = m.group(2).strip()
    # If fmt_arg is a quoted string, convert date-fns tokens to strftime
    if fmt_arg.startswith(("'", '"')):
        fmt_str = fmt_arg.strip("'\"")
        py_fmt = (
            fmt_str
            .replace("yyyy", "%Y")
            .replace("MM", "%m")
            .replace("dd", "%d")
            .replace("HH", "%H")
            .replace("mm", "%M")
            .replace("ss", "%S")
        )
        return f"{date_arg}.strftime('{py_fmt}')"
    # fmt_arg is a variable — emit strftime with the variable directly
    return f"{date_arg}.strftime({fmt_arg})"


def _translate_difference_in_days(m: re.Match[str]) -> str:
    a = m.group(1).strip()
    b = m.group(2).strip()
    return f"({a} - {b}).days"


def _translate_is_before(m: re.Match[str]) -> str:
    a = m.group(1).strip()
    b = m.group(2).strip()
    return f"{a} < {b}"


def _translate_is_after(m: re.Match[str]) -> str:
    a = m.group(1).strip()
    b = m.group(2).strip()
    return f"{a} > {b}"


def _translate_add_milliseconds(m: re.Match[str]) -> str:
    d = m.group(1).strip()
    ms = m.group(2).strip()
    return f"{d} + timedelta(milliseconds={ms})"


def _translate_each_day_of_interval(m: re.Match[str]) -> str:
    # eachDayOfInterval({start, end}) or eachDayOfInterval({start, end}, {step})
    inner = m.group(1).strip()
    start_m = re.search(r"start\s*:\s*(\w+)", inner)
    end_m = re.search(r"end\s*:\s*(\w+)", inner)
    start = start_m.group(1) if start_m else "start"
    end = end_m.group(1) if end_m else "end"
    step_group = m.group(2) if m.lastindex and m.lastindex >= 2 else None
    if step_group:
        step_m = re.search(r"\bstep\b", step_group)
        if step_m:
            return f"each_day_of_interval({start}, {end}, step=step)"
    return f"each_day_of_interval({start}, {end})"


def _translate_each_year_of_interval(m: re.Match[str]) -> str:
    inner = m.group(1).strip()
    start_m = re.search(r"start\s*:\s*(\w+)", inner)
    end_m = re.search(r"end\s*:\s*(\w+)", inner)
    start = start_m.group(1) if start_m else "start"
    end = end_m.group(1) if end_m else "end"
    return f"[datetime(y, 1, 1) for y in range({start}.year, {end}.year + 1)]"


def _translate_each_year_of_interval_var(m: re.Match[str]) -> str:
    """Translate eachYearOfInterval(varname) where varname is a variable."""
    var = m.group(1).strip()
    return f"[datetime(y, 1, 1) for y in range({var}['start'].year, {var}['end'].year + 1)]"


def _translate_start_of_day(m: re.Match[str]) -> str:
    d = m.group(1).strip()
    return f"{d}.replace(hour=0, minute=0, second=0, microsecond=0)"


def _translate_end_of_day(m: re.Match[str]) -> str:
    d = m.group(1).strip()
    return f"{d}.replace(hour=23, minute=59, second=59, microsecond=999999)"


def _translate_start_of_year(m: re.Match[str]) -> str:
    d = m.group(1).strip()
    return f"datetime({d}.year, 1, 1)"


def _translate_end_of_year(m: re.Match[str]) -> str:
    d = m.group(1).strip()
    return f"datetime({d}.year, 12, 31)"


def _translate_is_within_interval(m: re.Match[str]) -> str:
    d = m.group(1).strip()
    inner = m.group(2).strip()
    start_m = re.search(r"start\s*:\s*(\w+)", inner)
    end_m = re.search(r"end\s*:\s*(\w+)", inner)
    start = start_m.group(1) if start_m else "start"
    end = end_m.group(1) if end_m else "end"
    return f"{start} <= {d} <= {end}"


def _translate_sub_days(m: re.Match[str]) -> str:
    d = m.group(1).strip()
    n = m.group(2).strip()
    return f"{d} - timedelta(days={n})"


def _translate_is_this_year(m: re.Match[str]) -> str:
    d = m.group(1).strip()
    return f"{d}.year == datetime.now().year"


# Ordered list of (pattern, handler) pairs
_TRANSLATIONS: list[tuple[re.Pattern[str], object]] = [
    # format with quoted string arg or variable arg
    (re.compile(r"\bformat\s*\(\s*([^,]+),\s*(['\"][^'\"]+['\"]|\w+)\s*\)"), _translate_format),
    (re.compile(r"\bdifferenceInDays\s*\(\s*([^,]+),\s*([^)]+)\)"), _translate_difference_in_days),
    (re.compile(r"\bisBefore\s*\(\s*([^,]+),\s*([^)]+)\)"), _translate_is_before),
    (re.compile(r"\bisAfter\s*\(\s*([^,]+),\s*([^)]+)\)"), _translate_is_after),
    (re.compile(r"\baddMilliseconds\s*\(\s*([^,]+),\s*([^)]+)\)"), _translate_add_milliseconds),
    # eachDayOfInterval with optional {step} second arg
    (re.compile(r"\beachDayOfInterval\s*\(\s*(\{[^}]*\})\s*(?:,\s*(\{[^}]*\}))?\s*\)"), _translate_each_day_of_interval),
    # eachYearOfInterval with object literal
    (re.compile(r"\beachYearOfInterval\s*\(\s*(\{[^}]*\})\s*\)"), _translate_each_year_of_interval),
    # eachYearOfInterval with variable
    (re.compile(r"\beachYearOfInterval\s*\(\s*(\w+)\s*\)"), _translate_each_year_of_interval_var),
    (re.compile(r"\bstartOfDay\s*\(\s*([^)]+)\)"), _translate_start_of_day),
    (re.compile(r"\bendOfDay\s*\(\s*([^)]+)\)"), _translate_end_of_day),
    (re.compile(r"\bstartOfYear\s*\(\s*([^)]+)\)"), _translate_start_of_year),
    (re.compile(r"\bendOfYear\s*\(\s*([^)]+)\)"), _translate_end_of_year),
    (re.compile(r"\bisWithinInterval\s*\(\s*([^,]+),\s*(\{[^}]*\})\s*\)"), _translate_is_within_interval),
    (re.compile(r"\bsubDays\s*\(\s*([^,]+),\s*([^)]+)\)"), _translate_sub_days),
    (re.compile(r"\bisThisYear\s*\(\s*([^)]+)\)"), _translate_is_this_year),
]


def translate_date_function(ts_call: str) -> str:
    """Translate a date-fns function call string to Python datetime equivalent.

    Tries each known date-fns pattern in order and returns the first match.
    If no pattern matches, returns the original string unchanged and logs a
    warning.

    Args:
        ts_call: A TypeScript expression string containing a date-fns call.

    Returns:
        A Python expression string using ``datetime`` / ``timedelta``.
    """
    for pattern, handler in _TRANSLATIONS:
        m = pattern.search(ts_call)
        if m:
            result = handler(m)  # type: ignore[operator]
            logger.debug("translate_date_function: %r → %r", ts_call, result)
            return result

    logger.warning("translate_date_function: no pattern matched for %r", ts_call)
    return ts_call
