"""Collection utilities — Python equivalents of lodash helpers."""
from __future__ import annotations
import copy
from typing import Any, Callable, Iterable, TypeVar

T = TypeVar("T")
K = TypeVar("K")


def deep_copy(obj: T) -> T:
    """Deep clone an object. Equivalent to lodash cloneDeep."""
    return copy.deepcopy(obj)


def sort_by(items: Iterable[T], key_fn: Callable[[T], Any]) -> list[T]:
    """Sort items by key function. Equivalent to lodash sortBy."""
    return sorted(items, key=key_fn)


def group_by(items: Iterable[T], key_fn: Callable[[T], K]) -> dict[K, list[T]]:
    """Group items by key function. Equivalent to lodash groupBy."""
    result: dict[K, list[T]] = {}
    for item in items:
        key = key_fn(item)
        result.setdefault(key, []).append(item)
    return result


def uniq_by(items: Iterable[T], key_fn: Callable[[T], Any]) -> list[T]:
    """Return items with duplicates removed by key. Equivalent to lodash uniqBy."""
    seen: set = set()
    result = []
    for item in items:
        k = key_fn(item)
        if k not in seen:
            seen.add(k)
            result.append(item)
    return result


def sum_by(items: Iterable[T], key_fn: Callable[[T], float | int]) -> float:
    """Sum items by key function. Equivalent to lodash sumBy."""
    return sum(key_fn(item) for item in items)


# camelCase aliases used by translated code
cloneDeep = deep_copy
sortBy = sort_by
groupBy = group_by
uniqBy = uniq_by
sumBy = sum_by
