"""
Import path resolver for TypeScript-to-Python translation.

Resolves project-specific scoped import paths via a per-project
``tt_import_map.json`` file, and maps known third-party TypeScript
libraries (big.js, date-fns, lodash) to their Python equivalents.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Built-in third-party library mappings (NOT project-specific).
# Keys are TypeScript module specifiers; values are Python module names.
# Use None to suppress the import entirely.
_THIRD_PARTY_MAP: dict[str, str | None] = {
    "big.js": None,  # Big → Decimal; handled by big_mapper, no import needed
    "date-fns": None,  # date-fns functions handled by date_mapper
    "date-fns/format": None,
    "date-fns/differenceInDays": None,
    "date-fns/isBefore": None,
    "date-fns/isAfter": None,
    "date-fns/addMilliseconds": None,
    "date-fns/eachDayOfInterval": None,
    "date-fns/eachYearOfInterval": None,
    "date-fns/startOfDay": None,
    "date-fns/endOfDay": None,
    "date-fns/startOfYear": None,
    "date-fns/endOfYear": None,
    "date-fns/subDays": None,
    "date-fns/isWithinInterval": None,
    "date-fns/isThisYear": None,
    "lodash": None,  # lodash functions handled inline by transformer
    "lodash/sortBy": None,
    "lodash/cloneDeep": "copy",
    "lodash/isNumber": None,
}

# @nestjs/* modules are server-framework only — not needed in translation.
_NESTJS_PREFIX = "@nestjs/"


def load_import_map(path: Path) -> dict:
    """Load ``tt_import_map.json`` from the given directory path.

    Args:
        path: Directory that may contain ``tt_import_map.json``.

    Returns:
        Parsed JSON dict, or an empty dict if the file does not exist.
    """
    map_file = path / "tt_import_map.json"
    if not map_file.exists():
        logger.debug("tt_import_map.json not found at %s — using empty map", map_file)
        return {}
    try:
        return json.loads(map_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse tt_import_map.json at %s: %s", map_file, exc)
        return {}


def resolve(ts_import_path: str, import_map: dict) -> str | None:
    """Resolve a project-specific TS import path using the project import map.

    Args:
        ts_import_path: The TypeScript module specifier from the project source.
        import_map: Dict loaded from ``tt_import_map.json``.

    Returns:
        The Python module path string, or ``None`` if the path is not in the map.
    """
    entry = import_map.get(ts_import_path)
    if entry is None:
        return None
    return entry.get("python_module")


def resolve_third_party(module: str) -> str | None:
    """Map a known third-party TypeScript library to its Python equivalent.

    Built-in mappings cover big.js, date-fns, and lodash.
    ``@nestjs/*`` modules are intentionally omitted (server framework).
    Returns ``None`` for modules that should be suppressed (no import needed).

    Args:
        module: The TypeScript module specifier, e.g. ``"big.js"`` or
            ``"date-fns/format"``.

    Returns:
        The Python module name (e.g. ``"copy"``), ``None`` to suppress the
        import, or ``None`` if the module is unknown.
    """
    if module.startswith(_NESTJS_PREFIX):
        return None
    if module not in _THIRD_PARTY_MAP:
        return None
    return _THIRD_PARTY_MAP[module]


def generate_import_statement(python_module: str, symbols: list[str]) -> str:
    """Generate a Python import statement string.

    Args:
        python_module: The Python module to import from, e.g. ``"decimal"``.
        symbols: List of symbol names to import, e.g. ``["Decimal"]``.

    Returns:
        A Python import statement, e.g. ``"from decimal import Decimal"``.
        If ``symbols`` is empty, returns a bare ``"import <module>"`` statement.

    Examples:
        >>> generate_import_statement("decimal", ["Decimal"])
        'from decimal import Decimal'
        >>> generate_import_statement("datetime", [])
        'import datetime'
    """
    if not symbols:
        return f"import {python_module}"
    return f"from {python_module} import {', '.join(symbols)}"


def resolve_and_generate(
    ts_import_path: str,
    ts_symbols: list[str],
    import_map: dict,
) -> str:
    """Resolve a TypeScript import and generate the Python import statement.

    Tries the project import map first, then the built-in third-party map.
    Falls back to a commented placeholder for unmapped imports.

    Args:
        ts_import_path: The TypeScript module specifier.
        ts_symbols: List of TypeScript symbol names being imported.
        import_map: Dict loaded from ``tt_import_map.json``.

    Returns:
        A Python import statement string, or a commented placeholder:
        ``"# TODO: unmapped import: <ts_import_path>"`` if the path
        cannot be resolved.
    """
    # 1. Try project-specific map
    python_module = resolve(ts_import_path, import_map)
    if python_module is not None:
        entry = import_map.get(ts_import_path, {})
        symbol_map: dict = entry.get("symbols", {})
        if symbol_map:
            # Only include symbols explicitly mapped — skip unmapped ones
            py_symbols = [symbol_map[s] for s in ts_symbols if s in symbol_map]
            if not py_symbols and ts_symbols:
                # All symbols were filtered out — skip this import entirely
                return f"# skipped: no mapped symbols from {ts_import_path}"
        else:
            # Empty symbol map: emit bare module import (no specific symbols)
            py_symbols = []
        return generate_import_statement(python_module, py_symbols)

    # 2. Try built-in third-party map
    if ts_import_path in _THIRD_PARTY_MAP or ts_import_path.startswith(_NESTJS_PREFIX):
        third_party_module = resolve_third_party(ts_import_path)
        if third_party_module is None:
            # Intentionally suppressed (e.g. big.js, date-fns, lodash, @nestjs/*)
            return f"# suppressed: {ts_import_path}"
        return generate_import_statement(third_party_module, ts_symbols)

    # 3. Unmapped — emit a commented placeholder
    logger.warning("Unmapped import: %s", ts_import_path)
    return f"# TODO: unmapped import: {ts_import_path}"
