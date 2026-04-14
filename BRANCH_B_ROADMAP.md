# Branch B Roadmap — Translation Engines

---

## Branch identity

- **Branch name:** `feature/branch-b-engines`
- **Base branch:** `main` (after pre-branch setup is committed — see `PRE_BRANCH_SETUP.md`)
- **Merge target:** `main`
- **Merge order:** Either branch may merge first — no file conflicts possible

### Files Branch B owns (exhaustive)

Branch B is the **only** branch that may write to any of these:

```
tt/tt/parser.py                                 ← replaces stub committed in pre-branch setup
tt/tt/lib_map.py                                ← replaces stub committed in pre-branch setup
tt/tt/codegen.py                                ← replaces stub committed in pre-branch setup
tt/tt/scaffold/ghostfolio_pytx/tt_import_map.json  ← new file
tt/tests/__init__.py                            ← new directory + file
tt/tests/test_parser.py                         ← new
tt/tests/test_lib_map.py                        ← new
tt/tests/test_codegen.py                        ← new
```

### Files Branch B must never touch

```
tt/tt/cli.py                                    ← Branch A owns
tt/tt/runner.py                                 ← Branch A owns
tt/tt/translator.py                             ← Branch A owns
tt/tt/__init__.py                               ← Branch A owns
tt/tt/__main__.py                               ← Branch A owns
tt/pyproject.toml                               ← Branch A owns
tt/uv.lock                                      ← Branch A owns
tt/tt/scaffold/ghostfolio_pytx/.keep            ← Branch A owns
SOLUTION.md                                     ← Branch A owns
translations/ghostfolio_pytx/**                 ← Branch A owns (generated output)
contracts/**                                    ← read-only for both branches
```

### Dependency note — `python-dateutil`

Branch B's `lib_map.py` and `codegen.py` use `python-dateutil` at runtime. Branch A's A-1 milestone adds this dependency to `tt/pyproject.toml` on behalf of Branch B. Branch B must never touch `pyproject.toml`. Branch B's required packages are:

```
python-dateutil>=2.9    ← Branch A adds this to pyproject.toml in A-1
```

---

## Shared contracts (read-only reference)

These files are committed to `main` by the pre-branch setup before this branch is created.
**Neither branch may modify them.** Branch B reads them to understand what it must implement.

### `contracts/parse_tree_schema.py`

```python
"""Parse tree TypedDicts — the data contract between parser.py (Branch B) and
translator.py (Branch A). Branch B's parse_ts_file() must return a ParseTree.
Branch A's translator.py must consume it via this schema."""
from __future__ import annotations
from typing import TypedDict

class ParamNode(TypedDict):
    name: str
    ts_type: str          # raw TypeScript type string, e.g. "Big", "string", "Date"

class MethodNode(TypedDict):
    name: str             # camelCase, as written in TypeScript source
    visibility: str       # "public" | "protected" | "private" | ""
    params: list[ParamNode]
    return_type: str      # raw TypeScript return type string
    body_lines: list[str] # raw TypeScript body lines, untranslated

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
    symbols: list[str]    # e.g. ["Big"] from "import { Big } from 'big.js'"
    module: str           # e.g. "big.js" or "@ghostfolio/common/helper"

class ParseTree(TypedDict):
    classes: list[ClassNode]
    imports: list[ImportNode]
    top_level_vars: list[dict]   # {name: str, ts_type: str, initializer: str}
```

### `contracts/codegen_interface.py`

```python
"""Public function signatures for tt/tt/codegen.py (Branch B) that
tt/tt/translator.py (Branch A) calls. Names, parameters, and return types
are binding — do not change these without coordinating with Branch A."""
from __future__ import annotations
from contracts.parse_tree_schema import ParseTree, ClassNode, MethodNode

def generate_python_class(
    class_node: ClassNode,
    import_map: dict[str, str],
) -> str:
    """Return a complete Python class definition as a source string."""
    ...

def generate_imports(
    used_libraries: list[str],
    import_map: dict[str, str],
) -> str:
    """Return the Python import block as a source string."""
    ...

def camel_to_snake(name: str) -> str:
    """Convert camelCase identifier to snake_case. Pure function."""
    ...

def translate_expression(ts_expr: str) -> str:
    """Translate a single TypeScript expression string to Python."""
    ...
```

### `contracts/lib_map_interface.py`

```python
"""Type annotations for the mapping dicts in tt/tt/lib_map.py (Branch B).
Branch A's translator.py may import these dicts for runtime use."""

BIG_JS_METHODS: dict[str, str]      # ts_method_name -> python operator/pattern
DATE_FNS_FUNCTIONS: dict[str, str]  # ts_fn_name -> python equivalent
LODASH_FUNCTIONS: dict[str, str]    # ts_fn_name -> python equivalent
TS_TYPE_MAP: dict[str, str]         # ts_type_name -> python_type_name
PYTHON_IMPORTS: dict[str, list[str]] # category -> ["from x import y", ...]
```

### Stub files replaced by this branch

These stubs are committed to `main` before branching at the actual module paths. Branch B overwrites them with real implementations. Branch A uses them during development (imports succeed; implementations return stubs). After merge, Branch A's translator.py automatically picks up the real implementations since the module paths are identical.

| File | Stub behaviour | This branch provides |
|------|----------------|----------------------|
| `tt/tt/parser.py` | `parse_ts_file` returns empty `ParseTree`; `extract_class_methods` returns `[]` | Real regex/AST parser |
| `tt/tt/lib_map.py` | All dicts are `{}` | Complete mapping tables |
| `tt/tt/codegen.py` | `camel_to_snake` raises `NotImplementedError` | Real code generator |

---

## Milestones

B-1 and B-2 are **fully parallel** — they own different files and have no runtime dependency on each other. B-3 depends on both B-1 and B-2 completing first.

---

### Milestone B-1 — Build the TypeScript Parser

**Status:** [ ] Not started
**Agent:** Agent-B-Parser
**Dependencies:** None (first milestone — can start immediately after pre-branch setup)
**Scope:** `tt/tt/parser.py` (replaces stub), `tt/tests/__init__.py` (new), `tt/tests/test_parser.py` (new)
**Merge strategy:** Replaces stub file + two new files. Zero conflict with Branch A or B-2.

#### Goal
Implement a production-quality TypeScript parser that reads the two Ghostfolio calculator source files and returns a `ParseTree` conforming exactly to the `contracts/parse_tree_schema.py` TypedDicts. The parse tree feeds into B-3's code generator. Getting the method body extraction right is the critical path for translation correctness.

Target files to parse:
- `projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts`
- `projects/ghostfolio/apps/api/src/app/portfolio/calculator/portfolio-calculator.ts`

#### Tasks
- [ ] Read both TypeScript source files in full and catalogue every syntactic pattern present. Create a written inventory (as comments in `parser.py`) of all patterns to handle before writing any code:
  - `import { X, Y } from 'module'`
  - `export abstract class Foo { ... }` and `export class Foo extends Bar { ... }`
  - `private/protected/public methodName(params: Type): ReturnType { body }`
  - `private fieldName: Type;` and `private static readonly CONST = value;`
  - `const x: Type = new Big(0);`
  - `for (const item of collection) { ... }`
  - `if (condition) { ... } else { ... }`
  - `?.` optional chaining
  - `x ?? y` nullish coalescing
  - Arrow functions: `(x) => expr` and `(x): ReturnType => { body }`
  - Template literals: `` `text ${expr}` ``
  - TypeScript type destructuring in params: `{ start, end }: { start: Date; end: Date }`
  - `Big` arithmetic chains: `new Big(0).plus(x).div(y).toNumber()`
  - Index signatures: `{ [key: string]: Big }`
  - Generic types: `Array<T>`, `Record<string, T>`, `Promise<T>`
- [ ] Create `tt/tests/__init__.py` (empty) to make `tt/tests/` a Python package.
- [ ] Implement `tt/tt/parser.py` with these public functions (signatures match `contracts/codegen_interface.py`):
  - `parse_ts_file(path: Path) -> ParseTree`
  - `extract_class_methods(parse_tree: ParseTree, class_name: str) -> list[MethodNode]`
- [ ] Implementation strategy — use regex + bracket-depth tracking (no external AST libs needed, but tree-sitter is allowed):
  - Strip single-line comments `//` and block comments `/* */` before parsing (preserve line count)
  - Detect class boundaries via `{` / `}` depth counting
  - Extract method bodies by tracking brace depth from the opening `{` of each method
  - For each method, store `body_lines` as the raw TypeScript lines — do not translate here
  - Preserve original TypeScript type strings in `ts_type` fields — codegen (B-3) handles translation
- [ ] Methods that **must** appear in the parse tree output for `RoaiPortfolioCalculator` and its parent `PortfolioCalculator`:
  - `getSymbolMetrics` (largest method — ~300 lines in parent class)
  - `calculateOverallPerformance`
  - `getPerformanceCalculationType`
  - `getInvestments` (or equivalent — check both TS files)
  - `getSnapshot` / `getChartData` / `getHoldings` / `getPerformance` (parent class methods)
- [ ] Write `tt/tests/test_parser.py` with unit tests for each syntactic pattern above, using **inline TypeScript strings** (no file I/O needed in tests). Cover:
  - Class extraction: input `"export class Foo extends Bar { }"` → `ClassNode` with correct name and base class
  - Method extraction: visibility, params, return type, body lines
  - Import extraction: `"import { X } from 'y'"` → `ImportNode`
  - Optional chaining is preserved in `body_lines` unchanged
  - Nested braces in method body do not prematurely end the method

#### Acceptance criteria
- `parse_ts_file` parses both target TS files without raising exceptions.
- `extract_class_methods(tree, "RoaiPortfolioCalculator")` returns at least `getSymbolMetrics`, `calculateOverallPerformance`, `getPerformanceCalculationType`.
- `extract_class_methods(tree, "PortfolioCalculator")` returns at least `getInvestments`, `getChartData`, `getHoldings`, `getPerformance`.
- Return type conforms to `ParseTree` TypedDict (all required keys present).
- `pytest tt/tests/test_parser.py -v` — all tests pass.
- `make detect_rule_breaches` — no new violations.

#### Verification steps
- [ ] `pytest tt/tests/test_parser.py -v` — all tests pass
- [ ] `python -c "from tt.parser import parse_ts_file; from pathlib import Path; r = parse_ts_file(Path('projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts')); print([c['name'] for c in r['classes']])"` — `RoaiPortfolioCalculator` in output
- [ ] `python -c "from tt.parser import parse_ts_file, extract_class_methods; from pathlib import Path; r = parse_ts_file(Path('projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts')); methods = extract_class_methods(r, 'RoaiPortfolioCalculator'); print([m['name'] for m in methods])"` — `getSymbolMetrics` in output
- [ ] `make detect_rule_breaches` — no new violations

#### Changelog entry
- **Completed:** —
- **What was done:** —
- **Deviations:** —
- **Notes for merge:** —

---

### Milestone B-2 — Build the Library Mapping Tables

**Status:** [ ] Not started
**Agent:** Agent-B-LibMap
**Dependencies:** None (parallel with B-1 — no dependency between them)
**Scope:** `tt/tt/lib_map.py` (replaces stub), `tt/tt/scaffold/ghostfolio_pytx/tt_import_map.json` (new), `tt/tests/test_lib_map.py` (new)
**Merge strategy:** Replaces stub + two new files. Zero conflict with Branch A or B-1.

#### Goal
Provide complete, rule-compliant mapping tables covering every TypeScript library call found in both Ghostfolio calculator source files. These tables are the sole source of truth for expression translation — the code generator (B-3) imports them directly and must not contain hardcoded library strings.

The `tt_import_map.json` file ensures that no `@ghostfolio/` import path appears as a hardcode in any `tt/tt/` Python source file — satisfying Competition Rule 9.

#### Tasks
- [ ] Read both TypeScript source files and inventory **every** external library call:
  - All `Big.js` method calls (`.plus`, `.minus`, `.times`, `.div`, `.eq`, `.gt`, `.lt`, `.gte`, `.lte`, `.toNumber`, `.toFixed`, `.abs`, `.sqrt`, `.pow`, `.mod`, `Big.DP`, etc.)
  - All `date-fns` functions imported and used
  - All `lodash` functions imported and used (`sortBy`, `cloneDeep`, `sum`, `uniqBy`, `isNumber`, etc.)
  - All TypeScript built-in types used in method signatures and variable declarations
  - All `@ghostfolio/` import paths referenced in both files
- [ ] Implement `tt/tt/lib_map.py` with all five mapping dicts. For each dict, add a comment block above it explaining the translation pattern and listing any edge cases:

  **`BIG_JS_METHODS`** — maps Big.js method names to Python patterns. Note: Big.js arithmetic always uses `Decimal` in Python. Chaining (`.plus(x).div(y)`) must be handled by codegen. This dict provides the per-method Python operator/function.
  ```python
  BIG_JS_METHODS = {
      "plus": "+",
      "minus": "-",
      "times": "*",
      "div": "/",
      "eq": "==",
      "gt": ">",
      "lt": "<",
      "gte": ">=",
      "lte": "<=",
      "toNumber": "float",         # codegen wraps: float(x)
      "toFixed": "quantize",        # codegen generates: x.quantize(Decimal('0.' + '0'*n))
      "abs": "abs",                 # codegen wraps: abs(x)
      # ... complete from inventory
  }
  ```

  **`DATE_FNS_FUNCTIONS`** — maps date-fns function names to Python patterns. Many are operators rather than functions. Codegen uses these patterns to emit the correct Python.
  ```python
  DATE_FNS_FUNCTIONS = {
      "format":               "strftime",           # date.strftime('%Y-%m-%d')
      "differenceInDays":     "days_diff",          # (a - b).days  — ORDER: (later, earlier)
      "eachDayOfInterval":    "each_day",           # generator using timedelta(days=1)
      "eachYearOfInterval":   "each_year",          # generator using relativedelta(years=1)
      "isBefore":             "<",
      "isAfter":              ">",
      "isWithinInterval":     "within",             # start <= d <= end
      "startOfDay":           "date_only",          # date(d.year, d.month, d.day)
      "endOfDay":             "end_of_day",         # datetime(d.year, d.month, d.day, 23, 59, 59)
      "startOfYear":          "start_of_year",      # date(d.year, 1, 1)
      "endOfYear":            "end_of_year",        # date(d.year, 12, 31)
      "subDays":              "sub_days",           # d - timedelta(days=n)
      "addMilliseconds":      "add_ms",             # d + timedelta(milliseconds=n)
      "isThisYear":           "is_this_year",       # d.year == date.today().year
      "min":                  "min",
      # ... complete from inventory
  }
  ```

  **`LODASH_FUNCTIONS`** — maps lodash function names to Python equivalents.
  ```python
  LODASH_FUNCTIONS = {
      "sortBy":       "sorted_by",    # sorted(arr, key=lambda x: fn(x))
      "cloneDeep":    "deepcopy",     # copy.deepcopy(x)
      "sum":          "sum",          # sum(arr)
      "uniqBy":       "unique_by",    # list({fn(x): x for x in arr}.values())
      "isNumber":     "is_number",    # isinstance(x, (int, float, Decimal))
      # ... complete from inventory
  }
  ```

  **`TS_TYPE_MAP`** — maps TypeScript type strings to Python type strings.
  ```python
  TS_TYPE_MAP = {
      "Big":          "Decimal",
      "string":       "str",
      "number":       "float",
      "boolean":      "bool",
      "void":         "None",
      "any":          "Any",
      "Date":         "date",
      "never":        "NoReturn",
      "undefined":    "None",
      "null":         "None",
      # ... complete from inventory — include generic forms
  }
  ```

  **`PYTHON_IMPORTS`** — maps a library category name to the list of Python import lines needed.
  ```python
  PYTHON_IMPORTS = {
      "decimal":  ["from decimal import Decimal, ROUND_HALF_UP"],
      "datetime": ["from datetime import date, datetime, timedelta"],
      "dateutil": ["from dateutil.relativedelta import relativedelta"],
      "copy":     ["import copy"],
      "typing":   ["from typing import Any, Optional"],
      "math":     ["import math"],
      # ... complete from inventory
  }
  ```

- [ ] Populate `tt/tt/scaffold/ghostfolio_pytx/tt_import_map.json` with every `@ghostfolio/` import path found in both TS files. Map each to its Python module path. The JSON must be valid and have at least the following entries:
  ```json
  {
    "@ghostfolio/api/app/portfolio/calculator/portfolio-calculator":
        "app.wrapper.portfolio.calculator.portfolio_calculator",
    "@ghostfolio/common/interfaces":
        "app.wrapper.portfolio.interfaces",
    "@ghostfolio/common/types":
        "app.wrapper.portfolio.interfaces",
    "@ghostfolio/common/helper":
        "app.wrapper.portfolio.interfaces",
    "@ghostfolio/common/models":
        "app.wrapper.portfolio.interfaces",
    "@ghostfolio/api/helper/portfolio.helper":
        "app.wrapper.portfolio.interfaces"
  }
  ```
  Add all remaining `@ghostfolio/` paths found in the inventory.

- [ ] Write `tt/tests/test_lib_map.py` with assertions:
  - Each dict is non-empty
  - Spot-check: `BIG_JS_METHODS["plus"] == "+"`, `DATE_FNS_FUNCTIONS["isBefore"] == "<"`, `TS_TYPE_MAP["Big"] == "Decimal"`
  - Every `date-fns` function in the TS inventory has an entry in `DATE_FNS_FUNCTIONS`
  - Every `Big.js` method in the TS inventory has an entry in `BIG_JS_METHODS`
  - `PYTHON_IMPORTS["decimal"]` contains `"Decimal"` somewhere in the strings
  - `tt_import_map.json` is valid JSON and contains at least 5 entries (load from file in test)

#### Acceptance criteria
- `from tt.lib_map import BIG_JS_METHODS, DATE_FNS_FUNCTIONS, LODASH_FUNCTIONS, TS_TYPE_MAP, PYTHON_IMPORTS` imports without error.
- All Big.js methods found in the TS inventory have entries in `BIG_JS_METHODS`.
- All date-fns functions found in the TS inventory have entries in `DATE_FNS_FUNCTIONS`.
- `tt_import_map.json` is valid JSON with entries for all `@ghostfolio/` import paths in both TS files.
- `pytest tt/tests/test_lib_map.py -v` passes.
- `grep -r "@ghostfolio" tt/tt/*.py` returns zero matches (no hardcoded paths in Python source).
- `make detect_rule_breaches` shows `detect_direct_mappings: PASS`.

#### Verification steps
- [ ] `pytest tt/tests/test_lib_map.py -v` — all tests pass
- [ ] `python -c "from tt.lib_map import BIG_JS_METHODS; print(BIG_JS_METHODS['plus'])"` — prints `+`
- [ ] `python -c "import json; m = json.load(open('tt/tt/scaffold/ghostfolio_pytx/tt_import_map.json')); print(len(m), 'entries')"` — 6+ entries
- [ ] `grep -r "@ghostfolio" tt/tt/*.py` — zero matches
- [ ] `make detect_rule_breaches` — `detect_direct_mappings: PASS`

#### Changelog entry
- **Completed:** —
- **What was done:** —
- **Deviations:** —
- **Notes for merge:** —

---

### Milestone B-3 — Build the Python Code Generator

**Status:** [ ] Not started
**Agent:** Agent-B-Codegen
**Dependencies:** B-1 (parse tree schema must be concrete), B-2 (mapping tables must be complete)
**Scope:** `tt/tt/codegen.py` (replaces stub), `tt/tests/test_codegen.py` (new)
**Merge strategy:** Replaces stub + one new test file. Zero conflict with Branch A.

#### Goal
Implement the code generator that takes a `ParseTree` produced by `parser.py` and the mapping tables from `lib_map.py` and emits syntactically valid, semantically correct PEP-8 Python. This is the most complex module in Branch B — it handles all the mechanical transformation logic including Big.js chain rewriting, date-fns function substitution, TypeScript type erasure, and indentation.

All public function signatures must exactly match `contracts/codegen_interface.py`.

#### Tasks
- [ ] Start by implementing and testing `camel_to_snake(name: str) -> str` — this is used throughout and must be correct before anything else:
  - `getSymbolMetrics` → `get_symbol_metrics`
  - `calculateOverallPerformance` → `calculate_overall_performance`
  - `getPerformanceCalculationType` → `get_performance_calculation_type`
  - `totalInvestmentWithCurrencyEffect` → `total_investment_with_currency_effect`
  - Edge case: `getROAI` → `get_roai` (consecutive uppercase)

- [ ] Implement `translate_expression(ts_expr: str) -> str` handling these patterns (apply in this order to avoid double-substitution):
  1. `new Big(x)` → `Decimal(str(x))` — use string constructor to avoid float precision
  2. Big.js method chains: detect `.plus(`, `.minus(`, `.times(`, `.div(` and rewrite using `BIG_JS_METHODS`. For chained calls like `a.plus(b).div(c)`, convert to `(a + b) / c` with correct grouping.
  3. `.eq(x)` → `== x`, `.gt(x)` → `> x`, `.lt(x)` → `< x`, `.gte(x)` → `>= x`, `.lte(x)` → `<= x`
  4. `.toNumber()` → `float(...)` wrapping the receiver
  5. `.toFixed(n)` → quantize pattern using `ROUND_HALF_UP`
  6. `format(d, DATE_FORMAT)` → `d.strftime('%Y-%m-%d')` (DATE_FORMAT is a constant → fixed format)
  7. `differenceInDays(a, b)` → `(a - b).days`
  8. `eachDayOfInterval({start, end})` → emit a helper call or inline generator
  9. `eachYearOfInterval({start, end})` → emit a helper call or inline generator
  10. `isBefore(a, b)` → `a < b`, `isAfter(a, b)` → `a > b`
  11. `isWithinInterval(d, {start, end})` → `start <= d <= end`
  12. `sortBy(arr, fn)` → `sorted(arr, key=fn)`
  13. `cloneDeep(x)` → `copy.deepcopy(x)`
  14. `uniqBy(arr, fn)` → `list({fn(x): x for x in arr}.values())`
  15. Arrow functions `(x) => expr` → `lambda x: expr`; multi-param `(x, y) => expr` → `lambda x, y: expr`
  16. Template literals `` `text ${expr}` `` → `f"text {expr}"`
  17. `?.` optional chaining `a?.b` → `a.b if a is not None else None`
  18. `?? y` nullish coalescing `x ?? y` → `x if x is not None else y`
  19. `Object.keys(x)` → `list(x.keys())`; `Object.entries(x)` → `list(x.items())`; `Object.values(x)` → `list(x.values())`
  20. `Array.from(x)` → `list(x)`
  21. `[...arr]` spread copy → `list(arr)`
  22. `this.` → `self.`
  23. TypeScript `as Type` type assertions → remove (just keep the expression)
  24. `const x =` / `let x =` → `x =`
  25. Trailing `;` → remove

- [ ] Implement `generate_method(method_node: MethodNode) -> str` that:
  - Converts method name via `camel_to_snake`
  - Prepends `self` as first parameter
  - Translates each parameter type via `TS_TYPE_MAP`
  - Translates each body line via `translate_expression`
  - Preserves block structure (if/else, for, while) by tracking indentation
  - Adds `pass` if body is empty after translation
  - Returns the method as a properly indented string (4-space indent inside class)

- [ ] Implement `generate_python_class(class_node: ClassNode, import_map: dict[str, str]) -> str` that:
  - Emits `class ClassName(BaseName):` where base class name is looked up in `import_map` if needed
  - Emits each method from `class_node["methods"]` via `generate_method`
  - Returns the complete class as a string

- [ ] Implement `generate_imports(used_libraries: list[str], import_map: dict[str, str]) -> str` that:
  - Accepts a list of category keys (e.g. `["decimal", "datetime", "copy"]`)
  - Looks up each in `PYTHON_IMPORTS` and emits the import lines
  - Also emits `from <path> import <symbol>` for any cross-module imports from `import_map`
  - Deduplicates imports
  - Returns the complete import block

- [ ] Helper emitters for date-fns interval generators — since these can't be expressed as single expressions, emit inline helper functions at the top of the generated file:
  ```python
  # Emitted helpers (generated, not hardcoded in codegen.py):
  def _each_day(start, end):
      d = start
      while d <= end:
          yield d
          d += timedelta(days=1)

  def _each_year(start, end):
      d = start
      while d <= end:
          yield d
          d = d.replace(year=d.year + 1)
  ```
  Implement `generate_helper_functions() -> str` that returns these helpers as a string. `translator.py` (Branch A) calls this and prepends it to the output file.

- [ ] Write `tt/tests/test_codegen.py` with:
  - `test_camel_to_snake`: all the cases listed above including edge cases
  - `test_translate_expression_big_new`: `"new Big(0)"` → `"Decimal(str(0))"`
  - `test_translate_expression_chain`: `"new Big(0).plus(x).div(y)"` → correct Python with proper grouping
  - `test_translate_expression_this`: `"this.activities"` → `"self.activities"`
  - `test_translate_expression_optional_chain`: `"a?.b"` → `"a.b if a is not None else None"`
  - `test_translate_expression_arrow`: `"(x) => x.value"` → `"lambda x: x.value"`
  - `test_translate_expression_date_format`: `"format(d, DATE_FORMAT)"` → `"d.strftime('%Y-%m-%d')"`
  - `test_generate_method_simple`: given a trivial `MethodNode`, output passes `ast.parse()`
  - `test_generate_python_class_syntax`: given a minimal `ClassNode`, output passes `ast.parse()`
  - `test_generate_imports_dedup`: calling with duplicate categories produces no duplicate import lines

#### Acceptance criteria
- All functions exactly match the signatures in `contracts/codegen_interface.py`.
- `generate_python_class` produces output that `ast.parse()` accepts without error on all test inputs.
- `camel_to_snake` correctly handles all 5 test cases listed in the tasks.
- `translate_expression("new Big(0).plus(new Big(1)).toNumber()")` → valid Python that evaluates to `1.0` when `Decimal` is defined.
- `pytest tt/tests/test_codegen.py -v` — all tests pass.
- `make detect_rule_breaches` — no new violations.

#### Verification steps
- [ ] `pytest tt/tests/test_codegen.py -v` — all tests pass
- [ ] `python -c "from tt.codegen import camel_to_snake; assert camel_to_snake('getSymbolMetrics') == 'get_symbol_metrics'; print('ok')"`
- [ ] `python -c "from tt.codegen import camel_to_snake; assert camel_to_snake('calculateOverallPerformance') == 'calculate_overall_performance'; print('ok')"`
- [ ] `python -c "import ast; from tt.codegen import generate_python_class; src = generate_python_class({'name': 'Foo', 'base_class': None, 'methods': [], 'properties': []}, {}); ast.parse(src); print('syntax ok')"`
- [ ] `pytest tt/tests/` — B-1 and B-2 tests also still pass (no regressions)
- [ ] `make detect_rule_breaches` — no new violations

#### Changelog entry
- **Completed:** —
- **What was done:** —
- **Deviations:** —
- **Notes for merge:** —

---

## Dependency graph (Branch B internal)

```
B-1 (parser.py + test_parser.py)   ←── parallel ──→   B-2 (lib_map.py + tt_import_map.json + test_lib_map.py)
      │                                                       │
      └──────────────────────┬───────────────────────────────┘
                             │ (both must complete first)
                             ▼
                  B-3 (codegen.py + test_codegen.py)
```

B-1 and B-2 are **fully parallel** — separate agents may work on them simultaneously with zero coordination needed. B-3 may not begin until both B-1 and B-2 are complete (B-3 imports from both and its tests exercise both interfaces).

---

## Merge checklist for Branch B → `main`

### Pre-merge verification (run on Branch B before opening PR)
- [ ] `pytest tt/tests/test_parser.py -v` — all pass
- [ ] `pytest tt/tests/test_lib_map.py -v` — all pass
- [ ] `pytest tt/tests/test_codegen.py -v` — all pass
- [ ] `pytest tt/tests/` — all three test files pass together
- [ ] `make detect_rule_breaches` — all checks PASS, especially:
  - `detect_direct_mappings: PASS` (no `@ghostfolio/` in `tt/tt/*.py`)
  - `detect_llm_usage: PASS`
  - `detect_explicit_implementation: PASS`
- [ ] `grep -r "@ghostfolio" tt/tt/*.py` — zero matches

### Post-merge integration
- [ ] Confirm Branch A has been merged (or is merging simultaneously) — `tt/tt/translator.py` must call `parse_ts_file`, `generate_python_class`, `generate_helper_functions`, and `generate_imports`
- [ ] `python -c "from tt.parser import parse_ts_file; from tt.codegen import generate_python_class, generate_imports, generate_helper_functions; from tt.lib_map import BIG_JS_METHODS; print('all real engines loaded')"` — must not raise `NotImplementedError`
- [ ] `uv run --project tt tt translate` — exits 0, generates real (non-stub) output

### Full integration test
- [ ] `make translate-and-test-ghostfolio_pytx` — run and record `X passed / Y failed`
- [ ] `python -c "import ast; ast.parse(open('translations/ghostfolio_pytx/app/implementation/portfolio/calculator/roai/portfolio_calculator.py').read()); print('syntax ok')"`

### Iteration on `parser.py` and `codegen.py` (M6 — engines side)
- [ ] Analyse failing tests caused by parser defects (methods not extracted, body lines truncated, brace depth miscounted) — fix in `tt/tt/parser.py`
- [ ] Analyse failing tests caused by codegen defects (wrong expression translation, wrong indentation, broken Big.js chain rewriting) — fix in `tt/tt/codegen.py`
- [ ] Re-run `uv run --project tt tt translate && make translate-and-test-ghostfolio_pytx` after each fix
- [ ] Re-run `pytest tt/tests/` after each fix to verify no regressions in unit tests
- [ ] Run `make detect_rule_breaches` after every fix round

### Handoff to Branch A iteration
- [ ] Report to Branch A agents which failing tests are caused by orchestration issues in `translator.py` (e.g. wrong method list passed to generate, wrong output path, wrong import map loading) vs engine issues (parser/codegen defects)

### Post-merge tests
- [ ] `make detect_rule_breaches` — final clean run
- [ ] `pytest tt/tests/` — all unit tests pass on final main
- [ ] `make evaluate_tt_ghostfolio` — record combined score

---

## Changelog

| Milestone | Title | Completed | Summary |
|-----------|-------|-----------|---------|
| B-1 | Build the TypeScript Parser | — | — |
| B-2 | Build the Library Mapping Tables | — | — |
| B-3 | Build the Python Code Generator | — | — |
