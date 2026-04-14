"""
Import path resolver for TypeScript-to-Python translation.

Resolves ``@ghostfolio/...`` import paths via a project-specific
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
_THIRD_PARTY_MAP: dict[str, str | None] = {
    "big.js": "decimal",
    "date-fns": "datetime",
    "date-fns/format": "datetime",
    "date-fns/differenceInDays": "datetime",
    "date-fns/isBefore": "datetime",
    "date-fns/isAfter": "datetime",
    "date-fns/addMilliseconds": "datetime",
    "date-fns/eachDayOfInterval": "datetime",
    "date-fns/eachYearOfInterval": "datetime",
    "date-fns/startOfDay": "datetime",
    "date-fns/endOfDay": "datetime",
    "date-fns/startOfYear": "datetime",
    "date-fns/endOfYear": "datetime",
    "date-fns/subDays": "datetime",
    "date-fns/isWithinInterval": "datetime",
    "date-fns/isThisYear": "datetime",
    "lodash": "builtins",
    "lodash/sortBy": "builtins",
    "lodash/cloneDeep": "copy",
    "lodash/isNumber": "builtins",
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
    """Resolve a ``@ghostfolio/...`` import path using the project import map.

    Args:
        ts_import_path: The TypeScript module specifier, e.g.
            ``"@ghostfolio/common/interfaces"``.
        import_map: Dict loaded from ``tt_import_map.json``.

    Returns:
        The Python module path string (e.g. ``"app.wrapper.portfolio.interfaces"``),
        or ``None`` if the path is not in the map.
    """
    entry = import_map.get(ts_import_path)
    if entry is None:
        return None
    return entry.get("python_module")


def resolve_third_party(module: str) -> str | None:
    """Map a known third-party TypeScript library to its Python equivalent.

    Built-in mappings cover big.js, date-fns, and lodash.
    ``@nestjs/*`` modules are intentionally omitted (server framework).

    Args:
        module: The TypeScript module specifier, e.g. ``"big.js"`` or
            ``"date-fns/format"``.

    Returns:
        The Python module name (e.g. ``"decimal"``), or ``None`` if the
        module is unknown or intentionally unmapped.
    """
    if module.startswith(_NESTJS_PREFIX):
        return None
    result = _THIRD_PARTY_MAP.get(module)
    if result is None and module not in _THIRD_PARTY_MAP:
        return None
    return result


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
        py_symbols = [symbol_map.get(s, s) for s in ts_symbols] if ts_symbols else []
        return generate_import_statement(python_module, py_symbols)

    # 2. Try built-in third-party map
    third_party_module = resolve_third_party(ts_import_path)
    if third_party_module is not None:
        return generate_import_statement(third_party_module, ts_symbols)

    # 3. Unmapped — emit a commented placeholder
    logger.warning("Unmapped import: %s", ts_import_path)
    return f"# TODO: unmapped import: {ts_import_path}"
