"""TypeScript parser stub — replaced by Branch B (feature/branch-b-engines).

This stub has the correct signatures defined in contracts/codegen_interface.py.
Branch A (translator.py) can import from this module without errors.
All methods return empty/stub values until Branch B's real implementation merges.
"""
from __future__ import annotations
from pathlib import Path
from contracts.parse_tree_schema import ParseTree, MethodNode


def parse_ts_file(path: Path) -> ParseTree:
    """Stub — returns empty ParseTree. Branch B replaces this."""
    return {"classes": [], "imports": [], "top_level_vars": []}


def extract_class_methods(parse_tree: ParseTree, class_name: str) -> list[MethodNode]:
    """Stub — returns empty list. Branch B replaces this."""
    return []
