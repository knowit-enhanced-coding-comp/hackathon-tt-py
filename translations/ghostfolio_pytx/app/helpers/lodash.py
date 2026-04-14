"""lodash — Python equivalents of common lodash utility functions."""
from __future__ import annotations

import copy
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def clone_deep(obj: Any) -> Any:
    return copy.deepcopy(obj)


def sort_by(collection: list, key_fn: Callable) -> list:
    return sorted(collection, key=key_fn)


def uniq_by(collection: list, key_fn: Callable) -> list:
    seen = set()
    result = []
    for item in collection:
        k = key_fn(item)
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result


def group_by(collection: list, key_fn: Callable) -> dict:
    result: dict = {}
    for item in collection:
        k = key_fn(item)
        result.setdefault(k, []).append(item)
    return result


def flatten(collection: list) -> list:
    result = []
    for item in collection:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


def sum_by(collection: list, key_fn: Callable) -> float:
    return sum(key_fn(item) for item in collection)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def sum_values(values: list) -> float:
    return sum(float(v) for v in values)
