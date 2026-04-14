"""Clean up class-level TypeScript artifacts."""
from __future__ import annotations
import re
from tt.ir import ModuleIR

# Strip generic type parameters from base class names e.g. PortfolioCalculator<X, Y> → PortfolioCalculator
_GENERIC_RE = re.compile(r"<[^>]*>")


def rewrite_classes(ir: ModuleIR) -> ModuleIR:
    """
    Clean up class-level TS artifacts:
    - Strip type parameters from base class names.
    - Abstract classes are kept as-is (valid Python ABC).
    """
    for cls in ir.classes:
        cls.bases = [_strip_generics(b) for b in cls.bases]
    return ir


def _strip_generics(name: str) -> str:
    """Remove generic type parameters from a class name."""
    return _GENERIC_RE.sub("", name).strip()
