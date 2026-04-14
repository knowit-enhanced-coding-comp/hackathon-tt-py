# Pre-Branch Setup — Contracts and Shared Foundation

**Commit everything in this document to `main` before creating either feature branch.**

This setup establishes the shared interface contracts and stub implementations that allow Branch A and Branch B to develop independently with zero coordination during development. Once this commit lands on `main`, both branches are created from it and no further changes to contracts are permitted without agreement from both teams.

---

## Step 1 — Create the `contracts/` folder and define all shared interfaces

These files are **read-only** for both branches. Neither branch may modify them.

### `contracts/__init__.py`

Empty file to make `contracts/` importable.

### `contracts/parse_tree_schema.py`

```python
"""Parse tree TypedDicts — the data contract between:
  - parser.py (Branch B produces ParseTree)
  - translator.py (Branch A consumes ParseTree)

These TypedDicts define the exact shape of the dict returned by
parse_ts_file(). Branch B must return dicts that conform to this schema.
Branch A must only access keys defined in this schema.

DO NOT MODIFY after branching without agreement from both teams.
"""
from __future__ import annotations
from typing import TypedDict


class ParamNode(TypedDict):
    name: str
    ts_type: str       # raw TypeScript type string, e.g. "Big", "string", "Date"


class MethodNode(TypedDict):
    name: str          # camelCase, as written in TypeScript source
    visibility: str    # "public" | "protected" | "private" | ""
    params: list[ParamNode]
    return_type: str   # raw TypeScript return type string, e.g. "Big", "void"
    body_lines: list[str]  # raw TypeScript body lines, untranslated


class PropertyNode(TypedDict):
    name: str
    ts_type: str
    visibility: str
    is_static: bool


class ClassNode(TypedDict):
    name: str
    base_class: str | None
    methods: list[MethodNode]
    properties: list[PropertyNode]


class ImportNode(TypedDict):
    symbols: list[str]   # e.g. ["Big"] from "import { Big } from 'big.js'"
    module: str          # e.g. "big.js" or "@ghostfolio/common/helper"


class ParseTree(TypedDict):
    classes: list[ClassNode]
    imports: list[ImportNode]
    top_level_vars: list[dict]   # {name: str, ts_type: str, initializer: str}
```

### `contracts/codegen_interface.py`

```python
"""Public function signatures for tt/tt/codegen.py (implemented by Branch B,
called by Branch A's translator.py).

These signatures are BINDING. Branch B must implement each function with
exactly this name, parameter list, and return type. Branch A calls these
functions and must not be changed to accommodate a different signature.

DO NOT MODIFY after branching without agreement from both teams.
"""
from __future__ import annotations
from contracts.parse_tree_schema import ClassNode, MethodNode


def generate_python_class(
    class_node: ClassNode,
    import_map: dict[str, str],
) -> str:
    """Return a complete Python class definition as a source string.

    Args:
        class_node: A ClassNode from the parse tree (see parse_tree_schema.py).
        import_map: Contents of tt_import_map.json — maps @ghostfolio/ paths
                    to Python module paths.

    Returns:
        A string containing a valid Python class definition (not including
        imports). Must pass ast.parse() when combined with a valid import block.
    """
    ...


def generate_imports(
    used_libraries: list[str],
    import_map: dict[str, str],
) -> str:
    """Return the Python import block as a source string.

    Args:
        used_libraries: List of category keys from PYTHON_IMPORTS in lib_map.py,
                        e.g. ["decimal", "datetime", "copy"].
        import_map: Contents of tt_import_map.json.

    Returns:
        A string of Python import statements, one per line, deduplicated.
    """
    ...


def camel_to_snake(name: str) -> str:
    """Convert a camelCase identifier to snake_case.

    Examples:
        getSymbolMetrics             -> get_symbol_metrics
        calculateOverallPerformance  -> calculate_overall_performance
        getROAI                      -> get_roai

    Must be a pure function with no side effects.
    """
    ...


def translate_expression(ts_expr: str) -> str:
    """Translate a single TypeScript expression string to Python.

    Handles: Big.js arithmetic, date-fns calls, lodash calls, optional
    chaining, arrow functions, template literals, Object.keys/entries,
    this. -> self., const/let removal, trailing semicolons.

    Args:
        ts_expr: A single line or expression from a TypeScript method body.

    Returns:
        The Python equivalent as a string.
    """
    ...


def generate_helper_functions() -> str:
    """Return Python helper functions needed by the generated calculator.

    These are utility functions that replace TypeScript idioms which cannot
    be expressed as single-expression substitutions (e.g., eachDayOfInterval,
    eachYearOfInterval).

    Returns:
        A string of Python function definitions to be prepended to the
        generated output file, after the import block.
    """
    ...
```

### `contracts/lib_map_interface.py`

```python
"""Type annotations for the mapping dicts in tt/tt/lib_map.py (Branch B).

These names and types are the contract. Branch A's translator.py may import
any of these dicts for runtime use. Branch B must export them with exactly
these names and types.

DO NOT MODIFY after branching without agreement from both teams.
"""
from __future__ import annotations

# ts_method_name -> python operator or pattern string
# e.g. {"plus": "+", "toNumber": "float"}
BIG_JS_METHODS: dict[str, str]

# ts_fn_name -> python pattern key
# e.g. {"isBefore": "<", "format": "strftime"}
DATE_FNS_FUNCTIONS: dict[str, str]

# ts_fn_name -> python pattern key
# e.g. {"cloneDeep": "deepcopy", "sortBy": "sorted_by"}
LODASH_FUNCTIONS: dict[str, str]

# ts_type_name -> python_type_name
# e.g. {"Big": "Decimal", "string": "str", "Date": "date"}
TS_TYPE_MAP: dict[str, str]

# category_key -> list of Python import statement strings
# e.g. {"decimal": ["from decimal import Decimal, ROUND_HALF_UP"]}
PYTHON_IMPORTS: dict[str, list[str]]
```

---

## Step 2 — Create stub implementations at the real module paths

These stubs are committed to `main` so Branch A can import the modules during development. Branch B overwrites them with real implementations. The module paths are identical — after Branch B merges, Branch A's translator.py automatically uses the real code.

### `tt/tt/parser.py` (stub)

```python
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
```

### `tt/tt/lib_map.py` (stub)

```python
"""Library mapping tables stub — replaced by Branch B (feature/branch-b-engines).

All dicts are empty. Branch B populates them with the real mappings.
Branch A (translator.py) can import from this module without errors.
"""
from __future__ import annotations

BIG_JS_METHODS: dict[str, str] = {}
DATE_FNS_FUNCTIONS: dict[str, str] = {}
LODASH_FUNCTIONS: dict[str, str] = {}
TS_TYPE_MAP: dict[str, str] = {}
PYTHON_IMPORTS: dict[str, list[str]] = {}
```

### `tt/tt/codegen.py` (stub)

```python
"""Python code generator stub — replaced by Branch B (feature/branch-b-engines).

Stubs have the correct signatures. camel_to_snake and generate_python_class
raise NotImplementedError. Branch A can import this module without errors,
but cannot run an end-to-end translation until Branch B merges.
"""
from __future__ import annotations
from contracts.parse_tree_schema import ClassNode


def generate_python_class(
    class_node: ClassNode,
    import_map: dict[str, str],
) -> str:
    """Stub — raises NotImplementedError. Branch B replaces this."""
    raise NotImplementedError("codegen not yet implemented — awaiting Branch B merge")


def generate_imports(
    used_libraries: list[str],
    import_map: dict[str, str],
) -> str:
    """Stub — returns empty string. Branch B replaces this."""
    return ""


def camel_to_snake(name: str) -> str:
    """Stub — raises NotImplementedError. Branch B replaces this."""
    raise NotImplementedError("camel_to_snake not yet implemented — awaiting Branch B merge")


def translate_expression(ts_expr: str) -> str:
    """Stub — returns input unchanged. Branch B replaces this."""
    return ts_expr


def generate_helper_functions() -> str:
    """Stub — returns empty string. Branch B replaces this."""
    return ""
```

---

## Step 3 — Create empty tt_import_map.json placeholder

```json
{}
```

Path: `tt/tt/scaffold/ghostfolio_pytx/tt_import_map.json`

Branch B's B-2 milestone will populate this file. Branch A's translator.py reads it at runtime (empty during Branch A development — translator must handle the empty map gracefully by returning an empty import block, not crashing).

---

## Step 4 — Verify the contracts commit

Run these checks before branching:

- [ ] `python -c "from contracts.parse_tree_schema import ParseTree, ClassNode, MethodNode, ParamNode; print('contracts ok')"`
- [ ] `python -c "from tt.parser import parse_ts_file, extract_class_methods; print('parser stub ok')"`
- [ ] `python -c "from tt.lib_map import BIG_JS_METHODS, DATE_FNS_FUNCTIONS; print('lib_map stub ok')"`
- [ ] `python -c "from tt.codegen import generate_python_class, camel_to_snake; print('codegen stub importable')"`
- [ ] `python -c "import json; json.load(open('tt/tt/scaffold/ghostfolio_pytx/tt_import_map.json')); print('import map valid json')"`
- [ ] `uv run --project tt tt translate` — exits 0 (produces stub output — that is expected)
- [ ] `make detect_rule_breaches` — clean baseline

---

## Step 5 — Create both branches from this commit

```bash
# Confirm you are on main and it is clean
git status

# Create Branch A
git checkout -b feature/branch-a-pipeline
git push -u origin feature/branch-a-pipeline
git checkout main

# Create Branch B
git checkout -b feature/branch-b-engines
git push -u origin feature/branch-b-engines
git checkout main
```

Both branches now share this exact commit as their base. No further changes to `contracts/` or the stub files may be made on main without notifying both branch teams.

---

## File ownership summary

| File / folder | Owner | Notes |
|---|---|---|
| `contracts/` | Neither (pre-branch, read-only) | Committed to main, never modified |
| `tt/tt/cli.py` | Branch A | Modified in A-1 |
| `tt/tt/runner.py` | Branch A | New file in A-1 |
| `tt/tt/translator.py` | Branch A | Rewritten in A-2 |
| `tt/tt/__init__.py` | Branch A | Pre-existing, no changes |
| `tt/tt/__main__.py` | Branch A | Pre-existing, no changes |
| `tt/pyproject.toml` | Branch A | Modified in A-1 |
| `tt/uv.lock` | Branch A | Regenerated in A-1 |
| `tt/tt/scaffold/ghostfolio_pytx/.keep` | Branch A | Pre-existing, no changes |
| `SOLUTION.md` | Branch A | Written in A-3 |
| `translations/ghostfolio_pytx/` | Branch A | Generated output directory |
| `tt/tt/parser.py` | Branch B | Replaces stub |
| `tt/tt/lib_map.py` | Branch B | Replaces stub |
| `tt/tt/codegen.py` | Branch B | Replaces stub |
| `tt/tt/scaffold/ghostfolio_pytx/tt_import_map.json` | Branch B | Populated in B-2 |
| `tt/tests/__init__.py` | Branch B | New directory + file in B-1 |
| `tt/tests/test_parser.py` | Branch B | New in B-1 |
| `tt/tests/test_lib_map.py` | Branch B | New in B-2 |
| `tt/tests/test_codegen.py` | Branch B | New in B-3 |

**Read-only sources (neither branch modifies):**
- `projects/ghostfolio/**` — original TypeScript source
- `translations/ghostfolio_pytx_example/**` — reference skeleton
- `projecttests/ghostfolio_api/**` — API test suite
- `helptools/**` — build helpers
- `make/**` — Makefile fragments
- `COMPETITION_RULES.md` — competition rules

---

## Why this split produces zero merge conflicts

| Scenario | Result |
|---|---|
| Branch A merges first, then Branch B | Branch A adds runner.py, translator.py etc. Branch B then adds parser.py, lib_map.py, codegen.py. No file overlap. |
| Branch B merges first, then Branch A | Branch B replaces stubs with real implementations. Branch A then adds runner.py, translator.py etc. Translator now imports real implementations. No file overlap. |
| Both merge in same PR | Git merges two non-overlapping file sets. Zero conflicts guaranteed. |

The stub mechanism ensures that regardless of merge order, `translator.py` ends up importing the real implementations after both branches land on `main`.
