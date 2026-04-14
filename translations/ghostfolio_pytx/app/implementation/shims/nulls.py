"""Helpers for TypeScript nullish coalescing (??) and optional chaining (?.)."""
from __future__ import annotations
from typing import Any


def nullish(value: Any, fallback: Any) -> Any:
    """Return fallback if value is None or undefined-like, else value.
    Equivalent to TypeScript: value ?? fallback
    """
    return fallback if value is None else value


def safe_get(obj: Any, *keys: str, default: Any = None) -> Any:
    """Safely navigate nested attribute/key access.
    Equivalent to TypeScript: obj?.key1?.key2 ?? default
    """
    current = obj
    for key in keys:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(key)
        else:
            current = getattr(current, key, None)
    return current if current is not None else default
