"""
TypeScript to Python translator — AST pipeline.

Orchestrates the full Parse → Transform → Generate pipeline:
  1. Parse TypeScript source files with tree-sitter (parser.py)
  2. Extract classes and methods
  3. Translate each method body (transformer.py)
  4. Resolve imports (import_resolver.py)
  5. Generate Python source (generator.py)
  6. Write output files and __init__.py stubs
"""
from __future__ import annotations

import logging
from pathlib import Path

from tt import generator, import_resolver, parser, transformer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Source file paths (relative to repo root)
# ---------------------------------------------------------------------------

_ROAI_TS = (
    "projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts"
)
_BASE_TS = (
    "projects/ghostfolio/apps/api/src/app/portfolio/calculator/portfolio-calculator.ts"
)

# The 6 abstract methods that MUST appear in the output class
_REQUIRED_METHODS = [
    "get_performance",
    "get_investments",
    "get_holdings",
    "get_details",
    "get_dividends",
    "evaluate_report",
]

# Default parameter lists for required methods (used when not found in source)
_REQUIRED_METHOD_PARAMS: dict[str, list[str]] = {
    "get_performance": [],
    "get_investments": ["group_by=None"],
    "get_holdings": [],
    "get_details": ['base_currency="USD"'],
    "get_dividends": ["group_by=None"],
    "evaluate_report": [],
}


def _validate_python_body(body_lines: str, method_name: str) -> None:
    """Validate that a translated method body is syntactically valid Python.

    Wraps the body in a dummy function and attempts to parse it with ast.parse.

    Args:
        body_lines: The translated body source string.
        method_name: Method name for logging context.

    Raises:
        SyntaxError: If the body is not valid Python.
    """
    import ast
    wrapped = f"def _dummy():\n{body_lines}\n"
    try:
        ast.parse(wrapped)
    except SyntaxError as exc:
        raise SyntaxError(f"Invalid Python in {method_name}: {exc}") from exc


def _camel_to_snake(name: str) -> str:
    """Delegate to transformer's camel_to_snake."""
    return transformer.camel_to_snake(name)


def _translate_method(method: dict, source_bytes: bytes, context: dict) -> dict:
    """Translate a single method dict into a method_info dict for the generator.

    Args:
        method: Dict from parser.extract_methods — has ``name``, ``params``,
            ``return_type``, ``body_node``, ``access``.
        source_bytes: Raw TypeScript source bytes.
        context: Translation context passed to transformer.

    Returns:
        A method_info dict suitable for generator.generate_method.
    """
    ts_name = method["name"]
    py_name = _camel_to_snake(ts_name)

    # Translate parameter names to snake_case (strip type annotations)
    # Object/array destructured params become **kwargs
    py_params: list[str] = []
    for p in method.get("params", []):
        # params from parser are plain names (no type annotations)
        # Object patterns like {a, b} come through as "{a, b}" — replace with **kwargs
        stripped = p.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            py_params.append("**kwargs")
        else:
            py_params.append(_camel_to_snake(stripped))

    # Translate return type — sanitize complex/inline TS types
    ret_type: str | None = None
    if method.get("return_type"):
        raw_ret = method["return_type"]
        try:
            translated_ret = transformer.translate_type(raw_ret)
            # Validate it's a simple Python type annotation (no braces, semicolons)
            if "{" in translated_ret or ";" in translated_ret or "|" in translated_ret.replace("None", ""):
                ret_type = None  # too complex — omit annotation
            else:
                ret_type = translated_ret
        except Exception:  # noqa: BLE001
            ret_type = None

    # Translate body
    body_lines = ""
    body_node = method.get("body_node")
    if body_node is not None:
        try:
            body_lines = transformer.translate_method_body(
                body_node, source_bytes, context, indent=2
            )
            # Validate the translated body is syntactically valid Python
            _validate_python_body(body_lines, ts_name)
        except SyntaxError as exc:
            logger.warning("Syntax error in translated body of %s: %s", ts_name, exc)
            body_lines = "        pass  # TODO: translation produced invalid Python"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to translate body of %s: %s", ts_name, exc)
            body_lines = "        pass  # TODO: translation failed"

    return {
        "name": py_name,
        "params": py_params,
        "return_type": ret_type,
        "body_lines": body_lines,
    }


def _extract_methods_from_file(
    ts_path: Path,
    class_name_filter: str | None,
    context: dict,
    only_with_body: bool = False,
) -> tuple[list[dict], list[str]]:
    """Parse a TypeScript file and extract translated methods.

    Args:
        ts_path: Path to the TypeScript source file.
        class_name_filter: If set, only extract methods from this class.
        context: Translation context for the transformer.
        only_with_body: If True, skip abstract methods (no body_node).

    Returns:
        Tuple of (list of method_info dicts, list of TS import dicts).
    """
    if not ts_path.exists():
        logger.warning("TypeScript source not found: %s", ts_path)
        return [], []

    source_bytes = ts_path.read_bytes()
    tree = parser.parse_file(ts_path)
    root = tree.root_node

    ts_imports = parser.extract_imports(root)
    classes = parser.extract_classes(root)

    methods_out: list[dict] = []

    for cls in classes:
        if class_name_filter and cls["name"] != class_name_filter:
            continue
        raw_methods = parser.extract_methods(cls["node"])
        for m in raw_methods:
            if only_with_body and m.get("body_node") is None:
                continue
            method_info = _translate_method(m, source_bytes, context)
            methods_out.append(method_info)

    return methods_out, ts_imports


def _build_import_statements(ts_imports: list[dict], import_map: dict) -> list[str]:
    """Resolve TypeScript imports to Python import statements.

    Args:
        ts_imports: List of import dicts from parser.extract_imports.
        import_map: Loaded tt_import_map.json dict.

    Returns:
        List of Python import statement strings.
    """
    stmts: list[str] = []
    for imp in ts_imports:
        module_path = imp.get("module_path", "")
        symbols = imp.get("symbols", [])
        stmt = import_resolver.resolve_and_generate(module_path, symbols, import_map)
        stmts.append(stmt)
    return stmts


def _ensure_required_methods(methods: list[dict]) -> list[dict]:
    """Ensure all 6 required abstract methods are present.

    If a method is missing, add a stub with ``pass`` body.

    Args:
        methods: List of method_info dicts already translated.

    Returns:
        Updated list with all required methods present.
    """
    present = {m["name"] for m in methods}
    for req in _REQUIRED_METHODS:
        if req not in present:
            logger.info("Adding stub for missing required method: %s", req)
            methods.append({
                "name": req,
                "params": _REQUIRED_METHOD_PARAMS.get(req, []),
                "return_type": None,
                "body_lines": "        pass  # TODO: not found in TypeScript source",
            })
    return methods


def run_translation(repo_root: Path, output_dir: Path) -> None:
    """Run the full AST-based translation pipeline.

    Parses both TypeScript source files, translates all methods, generates
    a Python module, and writes it to the output directory.

    Args:
        repo_root: Root of the repository (contains ``projects/``).
        output_dir: Translation output directory (e.g. ``translations/ghostfolio_pytx``).
    """
    roai_ts = repo_root / _ROAI_TS
    base_ts = repo_root / _BASE_TS

    # Load import map from output_dir (copied there by scaffold setup)
    imp_map = import_resolver.load_import_map(output_dir)
    if not imp_map:
        logger.warning("tt_import_map.json not found at %s — imports may be unresolved", output_dir)

    # Translation context
    context: dict = {
        "import_map": imp_map,
        "local_vars": {},
        "class_name": "RoaiPortfolioCalculator",
    }

    # --- Phase 1: Extract methods from ROAI calculator ---
    logger.info("Parsing ROAI calculator: %s", roai_ts)
    roai_methods, roai_ts_imports = _extract_methods_from_file(
        roai_ts,
        class_name_filter="RoaiPortfolioCalculator",
        context=context,
        only_with_body=False,
    )

    # --- Phase 2: Extract non-abstract methods from base class ---
    logger.info("Parsing base class: %s", base_ts)
    base_context = {**context, "class_name": "PortfolioCalculator"}
    base_methods, base_ts_imports = _extract_methods_from_file(
        base_ts,
        class_name_filter=None,  # take all classes
        context=base_context,
        only_with_body=True,  # skip abstract methods
    )

    # Merge: ROAI methods take priority; add base methods not already present
    roai_method_names = {m["name"] for m in roai_methods}
    for bm in base_methods:
        if bm["name"] not in roai_method_names:
            roai_methods.append(bm)

    # Ensure all 6 required methods are present
    all_methods = _ensure_required_methods(roai_methods)

    # --- Phase 3: Resolve imports ---
    all_ts_imports = roai_ts_imports + base_ts_imports
    resolved_imports = _build_import_statements(all_ts_imports, imp_map)

    # Always include essential Python imports
    essential_imports = [
        "import copy",
        "from decimal import Decimal",
        "from datetime import datetime, timedelta",
        "from app.wrapper.portfolio.calculator.portfolio_calculator import PortfolioCalculator",
    ]
    # Prepend essentials, then resolved (dedup happens in generate_module)
    all_imports = essential_imports + resolved_imports

    # --- Phase 4: Generate Python source ---
    class_info = {
        "name": "RoaiPortfolioCalculator",
        "base_class": "PortfolioCalculator",
        "methods": all_methods,
    }
    source = generator.generate_module(all_imports, [class_info])

    # --- Phase 5: Write output ---
    output_file = (
        output_dir
        / "app"
        / "implementation"
        / "portfolio"
        / "calculator"
        / "roai"
        / "portfolio_calculator.py"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(source, encoding="utf-8")
    logger.info("Wrote translated output to %s", output_file)

    # --- Phase 6: Create __init__.py files ---
    generator.write_init_files(output_dir / "app" / "implementation")
    logger.info("Translation complete.")
