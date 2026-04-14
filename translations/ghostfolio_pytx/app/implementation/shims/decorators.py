"""No-op decorator stubs for NestJS/Angular-style decorators."""
from __future__ import annotations
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])
C = TypeVar("C", bound=type)


def injectable(*args: Any, **kwargs: Any) -> Callable[[C], C]:
    """No-op stub for @Injectable() — marks class as dependency-injectable."""
    def decorator(cls: C) -> C:
        cls.__di_metadata__ = getattr(cls, "__di_metadata__", {})
        cls.__di_metadata__["injectable"] = True
        return cls
    return decorator


def controller(path: str = "", *args: Any, **kwargs: Any) -> Callable[[C], C]:
    """No-op stub for @Controller() — marks class with route prefix."""
    def decorator(cls: C) -> C:
        cls.__di_metadata__ = getattr(cls, "__di_metadata__", {})
        cls.__di_metadata__["controller"] = path
        return cls
    return decorator


def log_performance(*args: Any, **kwargs: Any) -> Callable[[F], F]:
    """No-op stub for @LogPerformance — passthrough decorator."""
    def decorator(fn: F) -> F:
        return fn
    return decorator
