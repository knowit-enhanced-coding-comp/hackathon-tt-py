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
