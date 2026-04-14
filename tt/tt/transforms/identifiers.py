"""Identifier transforms for TypeScript to Python conversion.

Handles camelCase to snake_case conversion and keyword remapping.
"""

from __future__ import annotations

import re

# Pre-compiled pattern for camelCase boundary detection
_CAMEL_RE1 = re.compile(r"([A-Z]+)([A-Z][a-z])")
_CAMEL_RE2 = re.compile(r"([a-z0-9])([A-Z])")


def camel_to_snake(name: str) -> str:
    """Convert a camelCase or PascalCase name to snake_case."""
    s = _CAMEL_RE1.sub(r"\1_\2", name)
    s = _CAMEL_RE2.sub(r"\1_\2", s)
    return s.lower()


def to_py_ident(name: str) -> str:
    """Transform a TS identifier to its Python equivalent.

    - ``this`` becomes ``self``
    - camelCase becomes snake_case
    - Class names (PascalCase) are kept as-is
    """
    if name == "this":
        return "self"
    if name == "undefined":
        return "None"
    if name == "null":
        return "None"
    if name == "true":
        return "True"
    if name == "false":
        return "False"
    if name == "Number.EPSILON":
        return "1e-14"
    # Keep class names (start with upper, not ALL_CAPS)
    if name[0:1].isupper() and not name.isupper():
        return name
    return camel_to_snake(name)
