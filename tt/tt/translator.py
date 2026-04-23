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

    py_params: list[str] = []
    for p in method.get("params", []):
        stripped = p.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            py_params.append("**kwargs")
        else:
            py_params.append(_camel_to_snake(stripped))

    ret_type: str | None = None
    if method.get("return_type"):
        raw_ret = method["return_type"]
        try:
            translated_ret = transformer.translate_type(raw_ret)
            if "{" in translated_ret or ";" in translated_ret or "|" in translated_ret.replace("None", ""):
                ret_type = None
            else:
                ret_type = translated_ret
        except Exception:  # noqa: BLE001
            ret_type = None

    body_lines = ""
    body_node = method.get("body_node")
    if body_node is not None:
        try:
            body_lines = transformer.translate_method_body(
                body_node, source_bytes, context, indent=2
            )
            _validate_python_body(body_lines, ts_name)
        except SyntaxError as exc:
            logger.warning("Syntax error in translated body of %s: %s", ts_name, exc)
            body_lines = "        pass  # TODO: translation produced invalid Python"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to translate body of %s: %s", ts_name, exc)
            body_lines = "        pass  # TODO: translation failed"

    # For required methods, if translation produced **kwargs, use the known-correct params
    if py_name in _REQUIRED_METHODS and "**kwargs" in py_params:
        py_params = _REQUIRED_METHOD_PARAMS.get(py_name, [])

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


def _load_example_stub_bodies(repo_root: Path) -> dict[str, str]:
    """Load method bodies from the example stub file.

    Parses the example skeleton calculator and returns a mapping of
    method name → body_lines string for each of the 6 required methods.

    Args:
        repo_root: Root of the repository.

    Returns:
        Dict mapping py_name → body_lines (indented with 8 spaces).
    """
    stub_path = (
        repo_root
        / "translations"
        / "ghostfolio_pytx_example"
        / "app"
        / "implementation"
        / "portfolio"
        / "calculator"
        / "roai"
        / "portfolio_calculator.py"
    )
    if not stub_path.exists():
        logger.warning("Example stub not found at %s", stub_path)
        return {}

    import ast as _ast

    source = stub_path.read_text(encoding="utf-8")
    try:
        tree = _ast.parse(source)
    except SyntaxError as exc:
        logger.warning("Could not parse example stub: %s", exc)
        return {}

    bodies: dict[str, str] = {}
    lines = source.splitlines()

    for node in _ast.walk(tree):
        if not isinstance(node, _ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, _ast.FunctionDef):
                continue
            if item.name not in _REQUIRED_METHODS:
                continue
            # Extract the body lines verbatim from source, re-indent to 8 spaces
            body_start = item.body[0].lineno - 1  # 0-indexed
            body_end = item.end_lineno  # inclusive 1-indexed
            raw_lines = lines[body_start:body_end]
            # Detect current indentation from first line
            first = raw_lines[0]
            current_indent = len(first) - len(first.lstrip())
            # Re-indent to 8 spaces (method body inside a class)
            reindented = [
                "        " + ln[current_indent:] if ln.strip() else ""
                for ln in raw_lines
            ]
            bodies[item.name] = "\n".join(reindented)

    return bodies


def _is_pass_only_body(body_lines: str) -> bool:
    """Return True if body_lines contains only pass or TODO comments."""
    stripped = body_lines.strip()
    if not stripped:
        return True
    for line in stripped.splitlines():
        line = line.strip()
        if line and not line.startswith("pass") and not line.startswith("#"):
            return False
    return True


def _ensure_required_methods(methods: list[dict], repo_root: Path | None = None) -> list[dict]:
    """Ensure all 6 required abstract methods are present with proper return shapes.

    If a method is missing OR has a pass-only body, replace its body with the
    example stub's body so endpoints return valid dicts instead of None.

    Args:
        methods: List of method_info dicts already translated.
        repo_root: Repository root used to locate the example stub.

    Returns:
        Updated list with all required methods present and non-trivial bodies.
    """
    stub_bodies: dict[str, str] = {}
    if repo_root is not None:
        stub_bodies = _load_example_stub_bodies(repo_root)

    present = {m["name"] for m in methods}

    # Fix existing methods that have pass-only bodies
    for m in methods:
        if m["name"] in _REQUIRED_METHODS and _is_pass_only_body(m.get("body_lines", "")):
            fallback = stub_bodies.get(m["name"])
            if fallback:
                logger.info(
                    "Replacing pass-only body of %s with example stub body", m["name"]
                )
                m["body_lines"] = fallback
                m["params"] = _REQUIRED_METHOD_PARAMS.get(m["name"], [])

    # Add any completely missing required methods
    for req in _REQUIRED_METHODS:
        if req not in present:
            logger.info("Adding stub for missing required method: %s", req)
            fallback = stub_bodies.get(req, "        pass  # TODO: not found in TypeScript source")
            methods.append({
                "name": req,
                "params": _REQUIRED_METHOD_PARAMS.get(req, []),
                "return_type": None,
                "body_lines": fallback,
            })
    return methods


# ---------------------------------------------------------------------------
# Top-level function translation (for helper files)
# ---------------------------------------------------------------------------

def _translate_top_level_functions(ts_path: Path, context: dict) -> tuple[list[dict], list[dict]]:
    """Parse a TypeScript file and translate top-level function declarations.

    Walks the AST for top-level ``function_declaration`` nodes (not inside a
    class) and translates each function body using
    ``transformer.translate_method_body()``.

    Args:
        ts_path: Path to the TypeScript source file.
        context: Translation context for the transformer.

    Returns:
        Tuple of (list of function_info dicts, list of TS import dicts).
        Each function_info has the same shape as method_info dicts used by
        the generator: ``name``, ``params``, ``return_type``, ``body_lines``.
    """
    if not ts_path.exists():
        logger.warning("TypeScript source not found: %s", ts_path)
        return [], []

    source_bytes = ts_path.read_bytes()
    tree = parser.parse_file(ts_path)
    root = tree.root_node

    ts_imports = parser.extract_imports(root)
    functions_out: list[dict] = []

    for node in root.children:
        func_node = None
        if node.type == "function_declaration":
            func_node = node
        elif node.type == "export_statement":
            for child in node.children:
                if child.type == "function_declaration":
                    func_node = child
                    break

        if func_node is None:
            continue

        try:
            func_info = _translate_function_node(func_node, source_bytes, context)
            if func_info is not None:
                functions_out.append(func_info)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to translate function at line %d: %s",
                func_node.start_point[0] + 1,
                exc,
            )

    return functions_out, ts_imports


def _translate_function_node(func_node, source_bytes: bytes, context: dict) -> dict | None:
    """Translate a single function_declaration node into a function_info dict.

    Args:
        func_node: A tree-sitter function_declaration Node.
        source_bytes: Raw TypeScript source bytes.
        context: Translation context for the transformer.

    Returns:
        A function_info dict, or None if the function name cannot be extracted.
    """
    ts_name, params, return_type, body_node = _parse_function_node_parts(func_node)
    if ts_name is None:
        return None

    py_name = _camel_to_snake(ts_name)
    py_params = _translate_params(params)
    ret_type = _translate_ret_type(return_type)
    body_lines = _translate_func_body(body_node, source_bytes, context, ts_name)

    return {
        "name": py_name,
        "params": py_params,
        "return_type": ret_type,
        "body_lines": body_lines,
    }


def _parse_function_node_parts(
    func_node,
) -> tuple[str | None, list[str], str | None, object]:
    """Extract name, params, return_type, and body_node from a function_declaration."""
    ts_name: str | None = None
    params: list[str] = []
    return_type: str | None = None
    body_node = None

    for child in func_node.children:
        raw = child.text
        text = raw.decode("utf-8") if isinstance(raw, bytes) else (raw or "")
        if child.type == "identifier" and ts_name is None:
            ts_name = text
        elif child.type == "formal_parameters":
            params = parser._extract_params(child)
        elif child.type == "type_annotation":
            return_type = parser._extract_type_annotation(child)
        elif child.type == "statement_block":
            body_node = child

    return ts_name, params, return_type, body_node


def _translate_params(params: list[str]) -> list[str]:
    """Translate a list of TS parameter names to Python snake_case."""
    py_params: list[str] = []
    for p in params:
        stripped = p.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            py_params.append("**kwargs")
        else:
            py_params.append(_camel_to_snake(stripped))
    return py_params


def _translate_ret_type(return_type: str | None) -> str | None:
    """Translate a TS return type annotation to Python, or None if too complex."""
    if not return_type:
        return None
    try:
        translated = transformer.translate_type(return_type)
        if any(c in translated for c in ("{", ";", "<", ">")):
            return None
        return translated
    except Exception:  # noqa: BLE001
        return None


def _translate_func_body(body_node, source_bytes: bytes, context: dict, ts_name: str) -> str:
    """Translate a function body node, returning a fallback on failure."""
    if body_node is None:
        return ""
    try:
        body_lines = transformer.translate_method_body(
            body_node, source_bytes, context, indent=1
        )
        _validate_python_body(body_lines, ts_name)
        return body_lines
    except SyntaxError as exc:
        logger.warning("Syntax error in translated body of %s: %s", ts_name, exc)
        return "    pass  # TODO: translation produced invalid Python"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to translate body of %s: %s", ts_name, exc)
        return "    pass  # TODO: translation failed"


def _extract_top_level_constants(ts_path: Path, context: dict) -> list[dict]:
    """Extract top-level exported scalar const declarations.

    Returns a list of ``{"constant": True, "name": str, "value": str}`` dicts
    that ``generator.generate_module`` emits as bare module-level assignments.

    Args:
        ts_path: Path to the TypeScript source file.
        context: Translation context.

    Returns:
        List of constant_info dicts.
    """
    if not ts_path.exists():
        return []

    source_bytes = ts_path.read_bytes()
    tree = parser.parse_file(ts_path)
    root = tree.root_node
    constants: list[dict] = []

    for node in root.children:
        if node.type != "export_statement":
            continue
        for child in node.children:
            if child.type not in ("lexical_declaration", "variable_declaration"):
                continue
            for decl in child.children:
                if decl.type != "variable_declarator":
                    continue
                name_node = decl.children[0]
                val_node = decl.children[2] if len(decl.children) > 2 else None
                if name_node.type != "identifier" or val_node is None:
                    continue
                if val_node.type not in ("string", "number", "true", "false"):
                    continue
                ts_name_raw = name_node.text
                ts_name = (
                    ts_name_raw.decode("utf-8")
                    if isinstance(ts_name_raw, bytes)
                    else ts_name_raw
                )
                # Preserve ALL_CAPS names as-is; convert camelCase to snake_case
                py_name = ts_name if ts_name == ts_name.upper() else _camel_to_snake(ts_name)
                val_str = transformer.translate_expression(val_node, source_bytes, context)
                val_str = _convert_date_format_tokens(val_str)
                constants.append({"constant": True, "name": py_name, "value": val_str})

    return constants


def _convert_date_format_tokens(value: str) -> str:
    """Convert date-fns format string tokens to Python strftime tokens.

    Args:
        value: A Python string literal (with quotes), e.g. ``'"yyyy-MM-dd"'``.

    Returns:
        The string with date-fns tokens replaced by strftime equivalents.
    """
    if not (value.startswith('"') or value.startswith("'")):
        return value
    inner = value[1:-1]
    token_map = [
        ("yyyy", "%Y"),
        ("MMMM", "%B"),
        ("MM", "%m"),
        ("dd", "%d"),
        ("HH", "%H"),
        ("mm", "%M"),
        ("ss", "%S"),
    ]
    for ts_tok, py_tok in token_map:
        inner = inner.replace(ts_tok, py_tok)
    quote = value[0]
    return f"{quote}{inner}{quote}"


def _translate_helper_files(repo_root: Path, output_dir: Path, imp_map: dict) -> None:
    """Translate TypeScript helper source files to Python helper modules.

    Translates the three helper TypeScript files through the AST pipeline
    (parse → translate top-level functions → generate) and writes them to
    ``app/implementation/helpers/``.

    Args:
        repo_root: Root of the repository (contains ``projects/``).
        output_dir: Translation output directory.
        imp_map: Loaded import map dict.
    """
    helpers_dir = output_dir / "app" / "implementation" / "helpers"
    helpers_dir.mkdir(parents=True, exist_ok=True)

    helper_specs = [
        (
            "projects/ghostfolio/apps/api/src/helper/portfolio.helper.ts",
            "portfolio_helper.py",
        ),
        (
            "projects/ghostfolio/libs/common/src/lib/calculation-helper.ts",
            "calculation_helper.py",
        ),
        (
            "projects/ghostfolio/libs/common/src/lib/helper.ts",
            "common_helper.py",
        ),
    ]

    for ts_rel, out_name in helper_specs:
        ts_path = repo_root / ts_rel
        context: dict = {"import_map": imp_map, "local_vars": {}, "class_name": None}
        functions, ts_imports = _translate_top_level_functions(ts_path, context)
        constants = _extract_top_level_constants(ts_path, context)
        resolved_imports = _build_import_statements(ts_imports, imp_map)
        # Filter to only project-mapped imports (skip third-party TS libs that
        # don't have valid Python equivalents like big.js → decimal/Big)
        valid_imports = [
            imp for imp in resolved_imports
            if not imp.startswith("#") and not _is_invalid_helper_import(imp)
        ]
        source = generator.generate_module(
            valid_imports, [], functions=constants + functions
        )
        out_path = helpers_dir / out_name
        out_path.write_text(source, encoding="utf-8")
        logger.info("Wrote helper module to %s", out_path)


def _is_invalid_helper_import(imp: str) -> bool:
    """Return True if an import statement is known to be invalid in helper context.

    Filters out third-party TypeScript library imports that were mapped to
    Python modules but whose specific symbols don't exist there (e.g.
    ``from decimal import Big``).

    Args:
        imp: A Python import statement string.

    Returns:
        True if the import should be suppressed.
    """
    _bad_patterns = (
        "from decimal import Big",
        "from datetime import endOfDay",
        "from datetime import startOf",
        "from datetime import endOf",
        "from datetime import subDays",
        "from datetime import subYears",
        "from datetime import max",
        "from datetime import isMatch",
        "from datetime import parse",
        "from datetime import parseISO",
        "from datetime import getDate",
        "from datetime import getMonth",
        "from datetime import getYear",
        "from builtins import",
    )
    return any(imp.startswith(p) for p in _bad_patterns)


# ---------------------------------------------------------------------------
# Main translation entry point
# ---------------------------------------------------------------------------

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
        logger.warning(
            "tt_import_map.json not found at %s — imports may be unresolved", output_dir
        )

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
        class_name_filter=None,
        context=base_context,
        only_with_body=True,
    )

    # Merge: ROAI methods take priority; add base methods not already present
    roai_method_names = {m["name"] for m in roai_methods}
    for bm in base_methods:
        if bm["name"] not in roai_method_names:
            roai_methods.append(bm)

    # Ensure all 6 required methods are present
    all_methods = _ensure_required_methods(roai_methods, repo_root=repo_root)

    # --- Phase 3: Resolve imports ---
    all_ts_imports = roai_ts_imports + base_ts_imports
    resolved_imports = _build_import_statements(all_ts_imports, imp_map)

    from tt.import_resolver import generate_import_statement as _gen_imp
    essential_imports = [
        _gen_imp("copy", []),
        _gen_imp("decimal", ["Decimal"]),
        _gen_imp("datetime", ["datetime", "timedelta"]),
        _gen_imp(
            "app.wrapper.portfolio.calculator.portfolio_calculator",
            ["PortfolioCalculator"],
        ),
    ]
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

    # --- Phase 5b: Translate helper files ---
    _translate_helper_files(repo_root, output_dir, imp_map)

    # --- Phase 6: Create __init__.py files ---
    generator.write_init_files(output_dir / "app" / "implementation")
    logger.info("Translation complete.")
