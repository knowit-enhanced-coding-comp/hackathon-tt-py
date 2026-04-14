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
